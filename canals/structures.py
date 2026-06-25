"""
نظام تصميم المنشآت الهيدروليكية للقنوات الترابية
Hydraulic Structures Design System for Earth Canals
===========================================================
يشمل: البوابات، السيفونات، كواسر الضغط، وأحواض التهدئة
المؤلف: خبير هندسة الموارد المائية
التاريخ: 2024
الإصدار: 2.0
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve, minimize_scalar, root
from scipy.interpolate import interp1d
from typing import Dict, List, Tuple, Optional, Union
import warnings
warnings.filterwarnings('ignore')

# ====================== الإعدادات ======================
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 12

class GateDesigner:
    """
    فئة تصميم البوابات الهيدروليكية
    """
    
    def __init__(self):
        self.g = 9.81  # تسارع الجاذبية
        self.water_density = 1000  # كثافة الماء كجم/م³
        
        # أنواع البوابات المتاحة
        self.gate_types = {
            'sluice': 'بوابة انزلاقية',
            'radial': 'بوابة قطاعية',
            'flap': 'بوابة قلابة',
            'slide': 'بوابة منزلقة'
        }
        
        # معاملات التصريف للبوابات
        self.discharge_coefficients = {
            'sluice': {'free': 0.61, 'submerged': 0.58},
            'radial': {'free': 0.65, 'submerged': 0.62},
            'flap': {'free': 0.55, 'submerged': 0.52}
        }
    
    def design_sluice_gate(self, Q: float, H_up: float, H_down: float = None,
                          gate_width: float = None, max_opening: float = 1.5) -> Dict:
        """
        تصميم البوابة الانزلاقية
        
        المعاملات:
        ----------
        Q : التصريف المطلوب (م³/ث)
        H_up : عمق المياه أعلى البوابة (م)
        H_down : عمق المياه أسفل البوابة (م) - للبوابات المغمورة
        gate_width : عرض البوابة (م) - إذا كان معروفاً
        max_opening : أقصى فتحة للبوابة (م)
        """
        
        # تحديد نوع التدفق
        if H_down is None or H_down <= 0:
            flow_type = 'free'
            Cd = self.discharge_coefficients['sluice']['free']
        else:
            flow_type = 'submerged'
            Cd = self.discharge_coefficients['sluice']['submerged']
        
        def calculate_opening(Q, H, w, Cd):
            """حساب فتحة البوابة المطلوبة"""
            # معادلة التصريف للبوابة الانزلاقية
            # Q = Cd * w * a * sqrt(2g * H)
            a = Q / (Cd * w * np.sqrt(2 * self.g * H))
            return a
        
        # إذا لم يتم تحديد عرض البوابة، نحدده بشكل مناسب
        if gate_width is None:
            # عادة يكون عرض البوابة حوالي 1.5-2.5 مرة من العمق
            gate_width = min(2.0 * H_up, 5.0)
        
        # حساب فتحة البوابة
        opening = calculate_opening(Q, H_up, gate_width, Cd)
        
        # التحقق من أن الفتحة ضمن الحدود المسموحة
        if opening > max_opening:
            # زيادة عرض البوابة إذا كانت الفتحة كبيرة جداً
            gate_width = Q / (Cd * max_opening * np.sqrt(2 * self.g * H_up))
            opening = max_opening
        
        # حساب القوى الهيدروليكية
        hydrostatic_force = 0.5 * self.water_density * self.g * H_up**2 * gate_width
        
        # حساب عزم الانحناء على البوابة
        bending_moment = hydrostatic_force * H_up / 3
        
        # تصميم سمك البوابة (تقريبي)
        allowable_stress = 165e6  # إجهاد مسموح للفولاذ (باسكال)
        required_thickness = np.sqrt(6 * bending_moment / (gate_width * allowable_stress))
        
        # حساب قوة الرفع المطلوبة
        friction_coefficient = 0.3  # معامل احتكاك تقريبي
        gate_weight = gate_width * H_up * required_thickness * 7850 * self.g  # وزن تقريبي
        lifting_force = friction_coefficient * hydrostatic_force + gate_weight
        
        results = {
            'gate_type': 'بوابة انزلاقية',
            'flow_type': 'حر' if flow_type == 'free' else 'مغمور',
            'gate_width': gate_width,
            'gate_height': H_up * 1.2,  # ارتفاع البوابة مع هامش أمان
            'opening': opening,
            'opening_ratio': opening / H_up,
            'discharge_coefficient': Cd,
            'hydrostatic_force': hydrostatic_force,
            'bending_moment': bending_moment,
            'required_thickness': required_thickness * 1000,  # تحويل إلى مم
            'lifting_force': lifting_force,
            'velocity_through_gate': Q / (gate_width * opening)
        }
        
        return results
    
    def design_radial_gate(self, Q: float, H_up: float, radius: float = None,
                          gate_width: float = None, angle: float = None) -> Dict:
        """
        تصميم البوابة القطاعية (Tainter Gate)
        
        المعاملات:
        ----------
        Q : التصريف (م³/ث)
        H_up : العمق أعلى البوابة (م)
        radius : نصف قطر البوابة (م)
        gate_width : عرض البوابة (م)
        angle : زاوية الفتح (درجات)
        """
        
        if gate_width is None:
            gate_width = 2.0 * H_up
        
        if radius is None:
            # نصف القطر النموذجي للبوابات القطاعية
            radius = 1.2 * H_up
        
        # معادلة التصريف للبوابة القطاعية
        Cd = self.discharge_coefficients['radial']['free']
        
        def solve_gate_parameters(params):
            a, theta = params  # a: الفتحة، theta: الزاوية
            # Q = Cd * w * a * sqrt(2g * (H - a/2))
            Q_calc = Cd * gate_width * a * np.sqrt(2 * self.g * (H_up - a/2))
            return Q_calc - Q
        
        # حل لإيجاد الفتحة والزاوية
        from scipy.optimize import fsolve
        initial_guess = [0.5, 30]  # تخمين مبدئي
        solution = fsolve(lambda x: [solve_gate_parameters(x), 
                                     x[1] - np.degrees(np.arccos(1 - x[0]/radius))], 
                         initial_guess)
        
        opening = solution[0]
        theta = solution[1]
        
        # حساب القوى
        hydrostatic_force = 0.5 * self.water_density * self.g * H_up**2 * gate_width
        
        # عزم الدوران على محور البوابة
        torque = hydrostatic_force * radius * np.sin(np.radians(theta/2))
        
        results = {
            'gate_type': 'بوابة قطاعية',
            'radius': radius,
            'gate_width': gate_width,
            'opening': opening,
            'angle_degrees': theta,
            'discharge_coefficient': Cd,
            'hydrostatic_force': hydrostatic_force,
            'torque': torque,
            'hoist_capacity': torque / radius  # قوة الرفع المطلوبة
        }
        
        return results
    
    def plot_gate_design(self, gate_results: Dict):
        """
        رسم تخطيطي لتصميم البوابة
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
        
        # رسم القوى الهيدروليكية
        gate_types = ['sluice', 'radial']
        forces = [
            gate_results.get('hydrostatic_force', 0) / 1000,  # كيلو نيوتن
            gate_results.get('torque', 0) / 1000  # كيلو نيوتن.متر
        ]
        
        ax1.bar(['القوة الهيدروستاتيكية', 'عزم الدوران'], forces, 
                color=['steelblue', 'coral'])
        ax1.set_ylabel('القيمة (كيلو نيوتن أو كيلو نيوتن.متر)')
        ax1.set_title('القوى المؤثرة على البوابة')
        ax1.grid(True, alpha=0.3)
        
        # رسم تخطيطي مبسط للبوابة
        ax2.set_xlim(-2, gate_results.get('gate_width', 4) + 2)
        ax2.set_ylim(-gate_results.get('gate_height', 3) - 1, 2)
        
        H = gate_results.get('gate_height', 3)
        w = gate_results.get('gate_width', 3)
        
        # رسم جسم البوابة
        rect = plt.Rectangle((0, 0), w, H, fill=True, alpha=0.3, 
                             color='gray', label='جسم البوابة')
        ax2.add_patch(rect)
        
        # رسم مستوى الماء
        ax2.axhline(y=H*0.8, color='blue', linewidth=2, alpha=0.5, 
                   label='مستوى الماء')
        ax2.fill_between([0, w], [H*0.8, H*0.8], [0, 0], 
                         alpha=0.2, color='blue')
        
        ax2.set_title('المخطط التخطيطي للبوابة')
        ax2.set_xlabel('العرض (م)')
        ax2.set_ylabel('الارتفاع (م)')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        ax2.set_aspect('equal')
        
        plt.tight_layout()
        plt.show()


class SiphonDesigner:
    """
    فئة تصميم السيفونات (البالوعات)
    """
    
    def __init__(self):
        self.g = 9.81
        self.water_density = 1000
        
        # معاملات الفقد في السيفونات
        self.loss_coefficients = {
            'entrance': 0.5,      # فاقد الدخول
            'exit': 1.0,          # فاقد الخروج
            'bend_90': 0.3,       # فاقد الكوع 90 درجة
            'bend_45': 0.2,       # فاقد الكوع 45 درجة
            'valve': 0.2          # فاقد المحبس
        }
    
    def design_siphon(self, Q: float, H_static: float, L_pipe: float,
                     D_pipe: float = None, n_manning: float = 0.013,
                     min_submergence: float = 1.0) -> Dict:
        """
        تصميم السيفون
        
        المعاملات:
        ----------
        Q : التصريف المطلوب (م³/ث)
        H_static : الفرق السكوني في المنسوب (م)
        L_pipe : طول الماسورة (م)
        D_pipe : قطر الماسورة (م) - إذا كان معروفاً
        n_manning : معامل مانينج للماسورة
        min_submergence : الحد الأدنى للغمر (م)
        """
        
        if D_pipe is None:
            # تقدير مبدئي للقطر بناءً على السرعة المثلى
            V_optimal = 2.0  # سرعة مثلى في السيفونات (م/ث)
            D_pipe = np.sqrt(4 * Q / (np.pi * V_optimal))
            D_pipe = np.ceil(D_pipe * 10) / 10  # تقريب لأقرب 0.1 متر
        
        # حساب المساحة والسرعة
        A_pipe = np.pi * D_pipe**2 / 4
        V_pipe = Q / A_pipe
        
        # حساب الفواقد الهيدروليكية
        losses = self._calculate_siphon_losses(V_pipe, D_pipe, L_pipe, n_manning)
        
        # التحقق من الطاقة المتاحة
        H_available = H_static
        H_required = losses['total_loss']
        
        # معامل التصريف الكلي
        Cd = np.sqrt(H_available / (H_available + losses['minor_losses']))
        
        # حساب الضغوط في السيفون
        pressure_distribution = self._calculate_pressure_distribution(
            H_static, L_pipe, D_pipe, V_pipe, n_manning
        )
        
        # التحقق من التكهف (Cavitation)
        vapor_pressure = 2340  # ضغط البخار للماء (باسكال) عند 20°م
        min_pressure = min(pressure_distribution['pressure'])
        cavitation_risk = min_pressure < vapor_pressure
        
        # تصميم حوض التهدئة عند مخرج السيفون
        stilling_basin = self._design_siphon_stilling_basin(Q, V_pipe, D_pipe)
        
        results = {
            'pipe_diameter': D_pipe,
            'pipe_area': A_pipe,
            'velocity': V_pipe,
            'Reynolds_number': V_pipe * D_pipe / 1e-6,
            'head_losses': losses,
            'discharge_coefficient': Cd,
            'available_head': H_available,
            'required_head': H_required,
            'flow_status': 'كافي' if H_available >= H_required else 'غير كافي',
            'pressure_distribution': pressure_distribution,
            'cavitation_risk': cavitation_risk,
            'min_submergence_required': min_submergence,
            'stilling_basin': stilling_basin,
            'efficiency': (H_available - H_required) / H_available * 100
        }
        
        return results
    
    def _calculate_siphon_losses(self, V: float, D: float, L: float, 
                                n: float) -> Dict:
        """
        حساب الفواقد في السيفون
        """
        R = D / 4  # نصف القطر الهيدروليكي
        
        # فاقد الاحتكاك (مانينج)
        S_f = (n * V / R**(2/3))**2
        friction_loss = S_f * L
        
        # الفواقد الثانوية
        entrance_loss = self.loss_coefficients['entrance'] * V**2 / (2 * self.g)
        bend_loss = 2 * self.loss_coefficients['bend_90'] * V**2 / (2 * self.g)
        exit_loss = self.loss_coefficients['exit'] * V**2 / (2 * self.g)
        
        minor_losses = entrance_loss + bend_loss + exit_loss
        total_loss = friction_loss + minor_losses
        
        return {
            'friction_loss': friction_loss,
            'entrance_loss': entrance_loss,
            'bend_loss': bend_loss,
            'exit_loss': exit_loss,
            'minor_losses': minor_losses,
            'total_loss': total_loss,
            'friction_slope': S_f
        }
    
    def _calculate_pressure_distribution(self, H: float, L: float, D: float,
                                        V: float, n: float) -> Dict:
        """
        حساب توزيع الضغوط على طول السيفون
        """
        x = np.linspace(0, L, 50)
        
        # حساب الفاقد على طول المسار
        R = D / 4
        S_f = (n * V / R**(2/3))**2
        h_f = S_f * x
        
        # الضغط النسبي (بالنسبة للضغط الجوي)
        # موجز: ضغط أقل من الجوي في السيفون
        z = H * (1 - x/L)  # ارتفاع تقريبي
        pressure = self.water_density * self.g * (z - h_f)
        
        return {
            'distance': x,
            'pressure': pressure,
            'pressure_head': pressure / (self.water_density * self.g),
            'min_pressure_location': x[np.argmin(pressure)]
        }
    
    def _design_siphon_stilling_basin(self, Q: float, V: float, D: float) -> Dict:
        """
        تصميم حوض تهدئة لمخرج السيفون
        """
        # حساب رقم فرود
        Fr = V / np.sqrt(self.g * D)
        
        # طول حوض التهدئة (معادلة USBR Type II)
        if Fr < 4.5:
            L_basin = D * (1.5 + 1.1 * Fr)
        else:
            L_basin = D * (2.0 + 1.3 * Fr)
        
        # عرض حوض التهدئة
        B_basin = max(2.5 * D, 3.0)
        
        # ارتفاع الحوائط الجانبية
        y2 = D * (np.sqrt(1 + 8 * Fr**2) - 1) / 2  # العمق المترافق
        wall_height = 1.2 * y2
        
        return {
            'basin_length': L_basin,
            'basin_width': B_basin,
            'wall_height': wall_height,
            'conjugate_depth': y2,
            'froude_number': Fr
        }
    
    def plot_siphon_design(self, siphon_results: Dict):
        """
        رسم تخطيطي لتصميم السيفون
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # رسم توزيع الضغوط
        pressure_dist = siphon_results['pressure_distribution']
        axes[0, 0].plot(pressure_dist['distance'], 
                       pressure_dist['pressure_head'], 
                       'b-', linewidth=2)
        axes[0, 0].axhline(y=0, color='red', linestyle='--', alpha=0.5)
        axes[0, 0].fill_between(pressure_dist['distance'], 
                               pressure_dist['pressure_head'], 
                               0, alpha=0.2, color='blue')
        axes[0, 0].set_xlabel('المسافة على طول السيفون (م)')
        axes[0, 0].set_ylabel('ضغط الماء (م)')
        axes[0, 0].set_title('توزيع الضغط على طول السيفون')
        axes[0, 0].grid(True, alpha=0.3)
        
        # رسم الفواقد
        losses = siphon_results['head_losses']
        loss_types = ['احتكاك', 'دخول', 'أكواع', 'خروج']
        loss_values = [losses['friction_loss'], losses['entrance_loss'],
                      losses['bend_loss'], losses['exit_loss']]
        
        axes[0, 1].bar(loss_types, loss_values, color=['steelblue', 'coral', 
                                                       'lightgreen', 'orange'])
        axes[0, 1].set_ylabel('الفاقد (م)')
        axes[0, 1].set_title('توزيع الفواقد الهيدروليكية')
        axes[0, 1].grid(True, alpha=0.3)
        
        # رسم مقارنة الطاقة
        labels = ['الطاقة المتاحة', 'الطاقة المطلوبة']
        values = [siphon_results['available_head'], 
                 siphon_results['required_head']]
        colors = ['green' if values[0] >= values[1] else 'red', 'orange']
        axes[1, 0].bar(labels, values, color=colors)
        axes[1, 0].set_ylabel('الطاقة (م)')
        axes[1, 0].set_title('مقارنة الطاقة المتاحة والمطلوبة')
        axes[1, 0].grid(True, alpha=0.3)
        
        # رسم تخطيطي مبسط
        ax = axes[1, 1]
        L = pressure_dist['distance'][-1]
        H = siphon_results['available_head']
        
        # رسم مسار السيفون
        x_points = [0, L*0.3, L*0.5, L*0.7, L]
        y_points = [0, -H*0.8, -H, -H*0.5, 0]
        
        ax.plot(x_points, y_points, 'b-', linewidth=3, label='مسار السيفون')
        ax.fill_between(x_points, y_points, -2, alpha=0.1, color='blue')
        
        # مستويات المياه
        ax.axhline(y=0, color='blue', linestyle='-', alpha=0.7, 
                  label='المستوى العلوي')
        ax.axhline(y=-H, color='blue', linestyle='--', alpha=0.5, 
                  label='المستوى السفلي')
        
        ax.set_xlabel('المسافة الأفقية (م)')
        ax.set_ylabel('المنسوب (م)')
        ax.set_title('المخطط التخطيطي للسيفون')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


class PressureBreakerDesigner:
    """
    فئة تصميم كواسر الضغط (Pressure Breakers)
    """
    
    def __init__(self):
        self.g = 9.81
        self.water_density = 1000  # kg/m^3
        
        # أنواع كواسر الضغط
        self.breaker_types = {
            'stilling_well': 'بئر تهدئة',
            'impact_basin': 'حوض تصادم',
            'cascade': 'شلال متدرج',
            'stepped_chute': 'مزلق مدرج'
        }
    
    def design_stilling_well(self, Q: float, H_total: float, 
                           D_pipe: float, n_stages: int = None) -> Dict:
        """
        تصميم بئر تهدئة (Stilling Well)
        
        المعاملات:
        ----------
        Q : التصريف (م³/ث)
        H_total : الفرق الكلي في المنسوب (م)
        D_pipe : قطر الماسورة الداخلة (م)
        n_stages : عدد المراحل (إذا كان معروفاً)
        """
        
        # حساب سرعة الدخول
        A_pipe = np.pi * D_pipe**2 / 4
        V_in = Q / A_pipe
        
        # تحديد عدد المراحل الأمثل
        if n_stages is None:
            # كل مرحلة تتحمل حوالي 3-5 متر من الضغط
            n_stages = max(1, int(np.ceil(H_total / 4.0)))
        
        H_per_stage = H_total / n_stages
        
        # تصميم كل مرحلة
        stages = []
        for i in range(n_stages):
            # قطر البئر (حوالي 3-5 أضعاف قطر الماسورة)
            D_well = 4.0 * D_pipe
            
            # ارتفاع البئر
            H_well = H_per_stage + 0.5  # إضافة هامش أمان
            
            # حساب الطاقة المفقودة في المرحلة
            V_stage = Q / (np.pi * D_well**2 / 4)
            energy_loss = (V_in**2 - V_stage**2) / (2 * self.g)
            
            # عمق المياه في البئر
            y_well = Q / (D_well * np.sqrt(self.g * H_per_stage))
            
            stage = {
                'stage_number': i + 1,
                'well_diameter': D_well,
                'well_height': H_well,
                'water_depth': y_well,
                'velocity': V_stage,
                'energy_loss': energy_loss,
                'pressure_head': H_per_stage
            }
            stages.append(stage)
            
            # تحديث سرعة الدخول للمرحلة التالية
            V_in = V_stage
        
        # حساب الكفاءة الكلية
        total_energy_loss = sum(stage['energy_loss'] for stage in stages)
        efficiency = (total_energy_loss / H_total) * 100
        
        results = {
            'breaker_type': 'بئر تهدئة',
            'number_of_stages': n_stages,
            'total_head': H_total,
            'head_per_stage': H_per_stage,
            'stages': stages,
            'total_energy_loss': total_energy_loss,
            'efficiency': efficiency,
            'required_area': np.pi * (stages[0]['well_diameter']/2)**2
        }
        
        return results
    
    def design_impact_basin(self, Q: float, H_total: float, 
                          V_jet: float = None) -> Dict:
        """
        تصميم حوض تصادم (Impact Basin)
        """
        
        if V_jet is None:
            # حساب سرعة النفاث
            V_jet = np.sqrt(2 * self.g * H_total * 0.95)  # 95% من الطاقة الكامنة
        
        # مساحة مقطع النفاث
        A_jet = Q / V_jet
        D_jet = np.sqrt(4 * A_jet / np.pi)
        
        # أبعاد الحوض (حسب USBR Type VI)
        basin_width = max(3 * D_jet, 2.0)  # عرض الحوض
        basin_length = 3 * D_jet + 0.5  # طول الحوض
        basin_depth = 2 * D_jet + 0.3  # عمق الحوض
        
        # ارتفاع الحوائط
        wall_height = basin_depth + 0.5  # إضافة فراغ حر
        
        # حساب كفاءة تبديد الطاقة
        V_out = Q / (basin_width * basin_depth)
        energy_dissipated = (V_jet**2 - V_out**2) / (2 * self.g)
        efficiency = (energy_dissipated / H_total) * 100
        
        # حساب قوى التصادم
        impact_force = self.water_density * Q * (V_jet - V_out)
        
        results = {
            'breaker_type': 'حوض تصادم',
            'jet_velocity': V_jet,
            'jet_diameter': D_jet,
            'basin_width': basin_width,
            'basin_length': basin_length,
            'basin_depth': basin_depth,
            'wall_height': wall_height,
            'outlet_velocity': V_out,
            'energy_dissipated': energy_dissipated,
            'efficiency': efficiency,
            'impact_force': impact_force / 1000  # كيلو نيوتن
        }
        
        return results
    
    def design_cascade(self, Q: float, H_total: float, L_total: float,
                      n_steps: int = None) -> Dict:
        """
        تصميم شلال متدرج (Cascade)
        
        المعاملات:
        ----------
        Q : التصريف (م³/ث)
        H_total : الفرق الكلي في المنسوب (م)
        L_total : الطول الأفقي الكلي (م)
        n_steps : عدد الدرجات
        """
        
        if n_steps is None:
            # ارتفاع الخطوة الأمثل حوالي 0.5-1.0 متر
            step_height = 0.75
            n_steps = max(3, int(np.ceil(H_total / step_height)))
        
        h_step = H_total / n_steps
        L_step = L_total / n_steps
        
        # حساب التصريف النوعي
        q = Q / 1.0  # لكل متر عرض (يمكن تعديله)
        
        # عمق المياه الحرج
        y_c = (q**2 / self.g)**(1/3)
        
        # تصميم الدرجات
        steps = []
        for i in range(n_steps):
            # عمق المياه على الدرجة
            if i == 0:
                y_step = y_c
            else:
                # حساب تقريبي للعمق
                y_step = 0.4 * h_step * (q**2 / (self.g * h_step**3))**0.2
            
            # سرعة المياه
            V_step = q / y_step
            
            # رقم فرود
            Fr = V_step / np.sqrt(self.g * y_step)
            
            # الطاقة المفقودة
            E_loss = h_step * (1 - 0.1 * Fr)  # تقريبي
            
            step = {
                'step_number': i + 1,
                'height': h_step,
                'length': L_step,
                'water_depth': y_step,
                'velocity': V_step,
                'froude_number': Fr,
                'energy_loss': E_loss,
                'flow_regime': 'سريان فوق حرج' if Fr > 1 else 'سريان تحت حرج'
            }
            steps.append(step)
        
        total_energy_loss = sum(step['energy_loss'] for step in steps)
        
        results = {
            'breaker_type': 'شلال متدرج',
            'number_of_steps': n_steps,
            'step_height': h_step,
            'step_length': L_step,
            'critical_depth': y_c,
            'steps': steps,
            'total_energy_loss': total_energy_loss,
            'efficiency': (total_energy_loss / H_total) * 100,
            'overall_slope': H_total / L_total
        }
        
        return results
    
    def design_optimal_breaker(self, Q: float, H_total: float, 
                              D_pipe: float = None, L_total: float = None,
                              breaker_type: str = 'auto') -> Dict:
        """
        اختيار وتصميم النوع الأمثل لكاسر الضغط
        """
        
        # تحديد النوع المناسب تلقائياً
        if breaker_type == 'auto':
            if H_total <= 5:
                recommended_type = 'impact_basin'
            elif H_total <= 15:
                recommended_type = 'stilling_well'
            else:
                recommended_type = 'cascade'
        else:
            recommended_type = breaker_type
        
        # تنفيذ التصميم حسب النوع المختار
        if recommended_type == 'stilling_well':
            if D_pipe is None:
                D_pipe = np.sqrt(4 * Q / (np.pi * 2.0))  # افتراض سرعة 2 م/ث
            return self.design_stilling_well(Q, H_total, D_pipe)
        
        elif recommended_type == 'impact_basin':
            return self.design_impact_basin(Q, H_total)
        
        elif recommended_type == 'cascade':
            if L_total is None:
                L_total = H_total * 3  # ميل 1:3
            return self.design_cascade(Q, H_total, L_total)
    
    def plot_breaker_comparison(self, Q: float, H_range: np.ndarray):
        """
        رسم مقارنة بين أنواع كواسر الضغط المختلفة
        """
        fig, axes = plt.subplots(1, 2, figsize=(14, 6))
        
        efficiencies = {'stilling_well': [], 'impact_basin': [], 'cascade': []}
        
        for H in H_range:
            # تصميم كل نوع
            well = self.design_stilling_well(Q, H, 1.0)
            basin = self.design_impact_basin(Q, H)
            cascade = self.design_cascade(Q, H, H*3)
            
            efficiencies['stilling_well'].append(well['efficiency'])
            efficiencies['impact_basin'].append(basin['efficiency'])
            efficiencies['cascade'].append(cascade['efficiency'])
        
        # رسم الكفاءة
        for breaker_type, eff in efficiencies.items():
            axes[0].plot(H_range, eff, linewidth=2, 
                        label=self.breaker_types.get(breaker_type, breaker_type))
        
        axes[0].set_xlabel('الفرق في المنسوب (م)')
        axes[0].set_ylabel('كفاءة تبديد الطاقة (%)')
        axes[0].set_title('مقارنة كفاءة كواسر الضغط')
        axes[0].legend()
        axes[0].grid(True, alpha=0.3)
        
        # رسم التوصية
        recommended = []
        for H in H_range:
            if H <= 5:
                recommended.append(0)  # impact_basin
            elif H <= 15:
                recommended.append(1)  # stilling_well
            else:
                recommended.append(2)  # cascade
        
        axes[1].plot(H_range, recommended, 'ro-', linewidth=2)
        axes[1].set_xlabel('الفرق في المنسوب (م)')
        axes[1].set_ylabel('النوع الموصى به')
        axes[1].set_yticks([0, 1, 2])
        axes[1].set_yticklabels(['حوض تصادم', 'بئر تهدئة', 'شلال متدرج'])
        axes[1].set_title('النوع الموصى به حسب ارتفاع الضغط')
        axes[1].grid(True, alpha=0.3)
        
        plt.tight_layout()
        plt.show()


class HydraulicStructuresSystem:
    """
    النظام المتكامل لتصميم المنشآت الهيدروليكية
    """
    
    def __init__(self):
        self.gate_designer = GateDesigner()
        self.siphon_designer = SiphonDesigner()
        self.pressure_breaker_designer = PressureBreakerDesigner()
        
        self.projects = {}
    
    def comprehensive_design(self, project_name: str, 
                           canal_data: Dict,
                           required_structures: List[str] = None) -> Dict:
        """
        تصميم شامل للمنشآت الهيدروليكية
        
        المعاملات:
        ----------
        project_name : اسم المشروع
        canal_data : بيانات القناة (من نظام EarthCanalDesigner)
        required_structures : قائمة المنشآت المطلوبة
        """
        
        print(f"\n{'='*70}")
        print(f"التصميم الشامل للمنشآت الهيدروليكية - {project_name}")
        print(f"{'='*70}")
        
        results = {'project_name': project_name}
        
        if required_structures is None:
            required_structures = ['gate', 'siphon', 'pressure_breaker']
        
        for structure in required_structures:
            if structure == 'gate':
                print("\n📌 تصميم البوابات:")
                print("-" * 40)
                
                # استخدام بيانات القناة لتصميم البوابات
                Q = canal_data.get('discharge', 10.0)
                H = canal_data.get('depth', 1.0)
                gate_results = self.gate_designer.design_sluice_gate(Q=Q, H_up=H)
                print(f"✓ عرض البوابة: {gate_results['gate_width']:.2f} م")
                print(f"✓ فتحة البوابة: {gate_results['opening']:.3f} م")
                results['gate'] = gate_results

            elif structure == 'siphon':
                print("\n📌 تصميم السيفونات:")
                print("-" * 40)
                Q = canal_data.get('discharge', 10.0)
                H = canal_data.get('static_head', 3.0)
                L = canal_data.get('pipe_length', 30.0)
                siphon_results = self.siphon_designer.design_siphon(Q=Q, H_static=H, L_pipe=L)
                print(f"✓ قطر الماسورة: {siphon_results['pipe_diameter']:.2f} م")
                print(f"✓ السرعة: {siphon_results['velocity']:.2f} م/ث")
                results['siphon'] = siphon_results

            elif structure == 'pressure_breaker':
                print("\n📌 تصميم كاسر الضغط:")
                print("-" * 40)
                Q = canal_data.get('discharge', 10.0)
                H = canal_data.get('static_head', 3.0)
                breaker = self.pressure_breaker_designer.design_optimal_breaker(Q=Q, H_total=H)
                print(f"✓ النوع: {breaker['breaker_type']}")
                print(f"✓ الكفاءة: {breaker['efficiency']:.1f} %")
                results['pressure_breaker'] = breaker

        return results


# ====================== تشغيل البرنامج ======================

if __name__ == "__main__":
    system = HydraulicStructuresSystem()
    print("نظام تصميم المنشآت الهيدروليكية - جاهز للتشغيل")
    print("Hydraulic Structures Design System - Ready")
