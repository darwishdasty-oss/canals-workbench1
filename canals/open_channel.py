"""
نظام التصميم الهيدروليكي المتكامل للقنوات المفتوحة
Advanced Hydraulic Design System for Open Channels
===========================================================
إصدار احترافي يجمع النظريات الهندسية والهيدروليكية المتقدمة
المؤلف: خبير هندسة الموارد المائية والهيدروليكا
التاريخ: 2024
الإصدار: 3.0 Professional
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve, root_scalar, minimize
from scipy.integrate import solve_ivp, quad
from scipy.interpolate import UnivariateSpline, interp1d
from dataclasses import dataclass, field
from typing import Dict, List, Tuple, Optional, Union, Callable
from enum import Enum
import warnings
warnings.filterwarnings('ignore')

# ====================== الإعدادات المتقدمة ======================
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 11
plt.rcParams['figure.dpi'] = 100
plt.rcParams['savefig.dpi'] = 150

# ====================== تعريف الأنواع الأساسية ======================

class ChannelType(Enum):
    """أنواع المقاطع العرضية للقنوات"""
    RECTANGULAR = "مستطيل"
    TRAPEZOIDAL = "شبه منحرف"
    TRIANGULAR = "مثلث"
    CIRCULAR = "دائري"
    PARABOLIC = "مكافئي"
    COMPOUND = "مركب"

class FlowRegime(Enum):
    """أنظمة التدفق"""
    SUBCRITICAL = "تحت حرج"
    CRITICAL = "حرج"
    SUPERCRITICAL = "فوق حرج"

@dataclass
class ChannelGeometry:
    """هندسة المقطع العرضي للقناة"""
    bottom_width: float = 0.0  # عرض القاع (م)
    side_slope: float = 0.0  # الميل الجانبي (أفقي:عمودي)
    diameter: float = 0.0  # القطر للقنوات الدائرية (م)
    depth: float = 0.0  # عمق المياه (م)
    channel_type: ChannelType = ChannelType.TRAPEZOIDAL
    
    def area(self, y: float = None) -> float:
        """حساب مساحة المقطع العرضي"""
        if y is None:
            y = self.depth
        
        if self.channel_type == ChannelType.RECTANGULAR:
            return self.bottom_width * y
        elif self.channel_type == ChannelType.TRAPEZOIDAL:
            return self.bottom_width * y + self.side_slope * y**2
        elif self.channel_type == ChannelType.TRIANGULAR:
            return self.side_slope * y**2
        elif self.channel_type == ChannelType.CIRCULAR:
            if y > self.diameter:
                y = self.diameter
            theta = 2 * np.arccos(1 - 2*y/self.diameter)
            return self.diameter**2 / 8 * (theta - np.sin(theta))
        elif self.channel_type == ChannelType.PARABOLIC:
            return 2/3 * self.bottom_width * y
        else:
            raise ValueError(f"نوع القناة غير معروف: {self.channel_type}")
    
    def wetted_perimeter(self, y: float = None) -> float:
        """حساب المحيط المبلل"""
        if y is None:
            y = self.depth
        
        if self.channel_type == ChannelType.RECTANGULAR:
            return self.bottom_width + 2 * y
        elif self.channel_type == ChannelType.TRAPEZOIDAL:
            return self.bottom_width + 2 * y * np.sqrt(1 + self.side_slope**2)
        elif self.channel_type == ChannelType.TRIANGULAR:
            return 2 * y * np.sqrt(1 + self.side_slope**2)
        elif self.channel_type == ChannelType.CIRCULAR:
            if y > self.diameter:
                y = self.diameter
            theta = 2 * np.arccos(1 - 2*y/self.diameter)
            return self.diameter * theta / 2
        elif self.channel_type == ChannelType.PARABOLIC:
            # تقريب للمحيط المبلل للقناة المكافئية
            return self.bottom_width + 8*y**2/(3*self.bottom_width)
        else:
            raise ValueError(f"نوع القناة غير معروف: {self.channel_type}")
    
    def hydraulic_radius(self, y: float = None) -> float:
        """حساب نصف القطر الهيدروليكي"""
        return self.area(y) / self.wetted_perimeter(y)
    
    def top_width(self, y: float = None) -> float:
        """حساب عرض السطح"""
        if y is None:
            y = self.depth
        
        if self.channel_type in [ChannelType.RECTANGULAR]:
            return self.bottom_width
        elif self.channel_type in [ChannelType.TRAPEZOIDAL, ChannelType.TRIANGULAR]:
            return self.bottom_width + 2 * self.side_slope * y
        elif self.channel_type == ChannelType.CIRCULAR:
            if y > self.diameter:
                y = self.diameter
            return 2 * np.sqrt(y * (self.diameter - y))
        elif self.channel_type == ChannelType.PARABOLIC:
            return self.bottom_width * np.sqrt(y/self.depth)
        else:
            raise ValueError(f"نوع القناة غير معروف: {self.channel_type}")
    
    def hydraulic_depth(self, y: float = None) -> float:
        """حساب العمق الهيدروليكي"""
        return self.area(y) / self.top_width(y)

@dataclass
class FlowParameters:
    """معاملات التدفق"""
    discharge: float  # التصريف (م³/ث)
    velocity: float = 0.0  # السرعة (م/ث)
    froude_number: float = 0.0  # رقم فرود
    reynolds_number: float = 0.0  # رقم رينولدز
    specific_energy: float = 0.0  # الطاقة النوعية (م)
    momentum: float = 0.0  # قوة الدفع (م³)
    regime: FlowRegime = FlowRegime.SUBCRITICAL

# ====================== نظام النظريات الهيدروليكية ======================

class HydraulicTheories:
    """مجموعة النظريات الهيدروليكية المتقدمة"""
    
    def __init__(self):
        self.g = 9.81  # تسارع الجاذبية (م/ث²)
        self.nu = 1e-6  # اللزوجة الحركية للماء (م²/ث)
        self.rho = 1000  # كثافة الماء (كجم/م³)
    
    def bernoulli_equation(self, y1: float, V1: float, z1: float,
                          y2: float, z2: float, h_loss: float = 0) -> Dict:
        """
        تطبيق معادلة برنولي بين نقطتين
        
        Parameters:
        -----------
        y1, y2 : عمق المياه عند النقطتين (م)
        V1 : سرعة المياه عند النقطة الأولى (م/ث)
        z1, z2 : منسوب القاع عند النقطتين (م)
        h_loss : فاقد الطاقة بين النقطتين (م)
        
        Returns:
        --------
        Dict : نتائج معادلة برنولي
        """
        # الطاقة الكلية عند النقطة الأولى
        E1 = y1 + V1**2/(2*self.g) + z1
        
        # حساب السرعة عند النقطة الثانية
        V2 = np.sqrt(2*self.g * (E1 - y2 - z2 - h_loss))
        
        # الطاقة الكلية عند النقطة الثانية
        E2 = y2 + V2**2/(2*self.g) + z2
        
        return {
            'energy_point1': E1,
            'energy_point2': E2,
            'velocity_point2': V2,
            'energy_loss': h_loss,
            'pressure_head1': y1,
            'velocity_head1': V1**2/(2*self.g),
            'pressure_head2': y2,
            'velocity_head2': V2**2/(2*self.g)
        }
    
    def manning_equation(self, geometry: ChannelGeometry, n: float, 
                        S: float, y: float = None) -> Dict:
        """
        تطبيق معادلة مانينج للتدفق المنتظم
        
        Parameters:
        -----------
        geometry : هندسة المقطع
        n : معامل مانينج للخشونة
        S : ميل القاع (م/م)
        y : عمق المياه (م)
        
        Returns:
        --------
        Dict : نتائج معادلة مانينج
        """
        if y is None:
            y = geometry.depth
        
        A = geometry.area(y)
        P = geometry.wetted_perimeter(y)
        R = A / P
        
        # حساب السرعة باستخدام معادلة مانينج
        V = (1/n) * R**(2/3) * np.sqrt(S)
        Q = A * V
        
        # حساب رقم فرود
        Fr = V / np.sqrt(self.g * geometry.hydraulic_depth(y))
        
        return {
            'velocity': V,
            'discharge': Q,
            'hydraulic_radius': R,
            'area': A,
            'wetted_perimeter': P,
            'froude_number': Fr,
            'regime': self.classify_flow(Fr)
        }
    
    def chezy_equation(self, geometry: ChannelGeometry, C: float, 
                      S: float, y: float = None) -> Dict:
        """
        تطبيق معادلة تشيز للتدفق المنتظم
        
        Parameters:
        -----------
        geometry : هندسة المقطع
        C : معامل تشيز (م^(1/2)/ث)
        S : ميل القاع (م/م)
        y : عمق المياه (م)
        
        Returns:
        --------
        Dict : نتائج معادلة تشيز
        """
        if y is None:
            y = geometry.depth
        
        A = geometry.area(y)
        P = geometry.wetted_perimeter(y)
        R = A / P
        
        # معادلة تشيز
        V = C * np.sqrt(R * S)
        Q = A * V
        
        # تحويل إلى معامل مانينج المكافئ
        n_equivalent = R**(1/6) / C
        
        return {
            'velocity': V,
            'discharge': Q,
            'hydraulic_radius': R,
            'chezy_coefficient': C,
            'equivalent_manning_n': n_equivalent,
            'froude_number': V / np.sqrt(self.g * geometry.hydraulic_depth(y))
        }
    
    def critical_flow_analysis(self, geometry: ChannelGeometry, 
                              Q: float = None) -> Dict:
        """
        تحليل التدفق الحرج
        
        Parameters:
        -----------
        geometry : هندسة المقطع
        Q : التصريف (إذا كان معروفاً)
        
        Returns:
        --------
        Dict : معاملات التدفق الحرج
        """
        def critical_condition(y):
            """شرط التدفق الحرج: Q²T/gA³ = 1"""
            A = geometry.area(y)
            T = geometry.top_width(y)
            if Q:
                return Q**2 * T / (self.g * A**3) - 1
            return 0
        
        # حل لإيجاد العمق الحرج
        if geometry.channel_type == ChannelType.RECTANGULAR:
            q = Q / geometry.bottom_width  # التصريف النوعي
            yc = (q**2 / self.g)**(1/3)
        else:
            # حل عددي للقنوات غير المستطيلة
            try:
                yc = root_scalar(critical_condition, 
                               bracket=[0.01, 10.0],
                               method='bisect').root
            except:
                yc = 1.0  # قيمة افتراضية
        
        Ac = geometry.area(yc)
        Vc = Q / Ac if Q else np.sqrt(self.g * geometry.hydraulic_depth(yc))
        Ec = yc + Vc**2/(2*self.g)
        
        return {
            'critical_depth': yc,
            'critical_velocity': Vc,
            'critical_area': Ac,
            'specific_energy_min': Ec,
            'froude_number': 1.0
        }
    
    def normal_depth_calculation(self, geometry: ChannelGeometry, 
                                Q: float, n: float, S: float) -> float:
        """
        حساب العمق الطبيعي (التدفق المنتظم)
        
        Parameters:
        -----------
        geometry : هندسة المقطع
        Q : التصريف (م³/ث)
        n : معامل مانينج
        S : ميل القاع
        
        Returns:
        --------
        float : العمق الطبيعي
        """
        def manning_function(y):
            A = geometry.area(y)
            P = geometry.wetted_perimeter(y)
            R = A / P
            return (1/n) * A * R**(2/3) * np.sqrt(S) - Q
        
        # حل عددي لإيجاد العمق الطبيعي
        try:
            yn = root_scalar(manning_function, 
                           bracket=[0.01, 20.0],
                           method='bisect').root
        except:
            # محاولة بطريقة نيوتن إذا فشل التنصيف
            try:
                yn = fsolve(manning_function, 1.0)[0]
            except:
                yn = 1.0
        
        return yn
    
    def gradually_varied_flow(self, geometry: ChannelGeometry, 
                            Q: float, n: float, S0: float,
                            y_start: float, L: float, 
                            n_points: int = 100) -> Dict:
        """
        تحليل التدفق المتغير تدريجياً (Gradually Varied Flow)
        
        Parameters:
        -----------
        geometry : هندسة المقطع
        Q : التصريف (م³/ث)
        n : معامل مانينج
        S0 : ميل القاع
        y_start : العمق الابتدائي
        L : طول القناة
        n_points : عدد نقاط الحساب
        
        Returns:
        --------
        Dict : ملامح سطح الماء
        """
        # حساب العمق الحرج والطبيعي
        yc = self.critical_flow_analysis(geometry, Q)['critical_depth']
        yn = self.normal_depth_calculation(geometry, Q, n, S0)
        
        def dy_dx(x, y):
            """معادلة التدفق المتغير تدريجياً"""
            A = geometry.area(y[0])
            P = geometry.wetted_perimeter(y[0])
            R = A / P
            T = geometry.top_width(y[0])
            
            # احتكاك القاع
            Sf = (n * Q / (A * R**(2/3)))**2
            
            # معادلة سطح الماء
            numerator = S0 - Sf
            denominator = 1 - Q**2 * T / (self.g * A**3)
            
            if abs(denominator) < 1e-10:
                return [0]  # تجنب القسمة على صفر عند العمق الحرج
            
            return [numerator / denominator]
        
        # حل المعادلة التفاضلية
        x_span = [0, L]
        x_eval = np.linspace(0, L, n_points)
        
        try:
            solution = solve_ivp(dy_dx, x_span, [y_start], 
                               method='RK45', t_eval=x_eval,
                               rtol=1e-6)
            
            if solution.success:
                water_surface = solution.y[0]
            else:
                water_surface = np.full(n_points, y_start)
        except:
            water_surface = np.full(n_points, y_start)
        
        # تصنيف منحنى سطح الماء
        curve_type = self.classify_gvf_curve(yn, yc, y_start)
        
        return {
            'distance': x_eval,
            'water_surface': water_surface,
            'normal_depth': yn,
            'critical_depth': yc,
            'bed_elevation': -S0 * x_eval,
            'curve_type': curve_type,
            'froude_profile': Q / (geometry.area(water_surface) * 
                           np.sqrt(self.g * geometry.hydraulic_depth(water_surface)))
        }
    
    def classify_flow(self, Fr: float) -> FlowRegime:
        """تصنيف نظام التدفق"""
        if Fr < 0.99:
            return FlowRegime.SUBCRITICAL
        elif Fr > 1.01:
            return FlowRegime.SUPERCRITICAL
        else:
            return FlowRegime.CRITICAL
    
    def classify_gvf_curve(self, yn: float, yc: float, y: float) -> str:
        """تصنيف منحنى التدفق المتغير تدريجياً"""
        if y > yn and y > yc:
            curve = "M1" if yn > yc else "S1"
        elif y < yn and y < yc:
            curve = "M3" if yn > yc else "S3"
        elif yn > y > yc:
            curve = "M2"
        elif yc > y > yn:
            curve = "S2"
        else:
            curve = "غير محدد"
        
        slope_type = "معتدل" if yn > yc else "حاد"
        return f"{curve} ({slope_type})"
    
    def energy_loss_calculation(self, V1: float, V2: float, 
                               y1: float, y2: float, loss_type: str = 'gradual') -> Dict:
        """
        حساب فقدان الطاقة في التمدد أو التقلص
        
        Parameters:
        -----------
        V1, V2 : السرعات (م/ث)
        y1, y2 : الأعماق (م)
        loss_type : نوع الفاقد ('gradual' أو 'sudden')
        
        Returns:
        --------
        Dict : فواقد الطاقة
        """
        # فرق الطاقة الحركية
        velocity_head_diff = abs(V1**2 - V2**2) / (2 * self.g)
        
        if loss_type == 'gradual':
            # فاقد تدريجي
            loss_coefficient = 0.1  # للتغير التدريجي
        elif loss_type == 'sudden_expansion':
            # فاقد التمدد المفاجئ
            loss_coefficient = ((V1 - V2)**2) / (2 * self.g * velocity_head_diff) if velocity_head_diff > 0 else 0.5
        elif loss_type == 'sudden_contraction':
            # فاقد التقلص المفاجئ
            A_ratio = min(y1, y2) / max(y1, y2)
            loss_coefficient = 0.5 * (1 - A_ratio)
        else:
            loss_coefficient = 0.0
        
        head_loss = loss_coefficient * velocity_head_diff
        power_loss = self.rho * self.g * head_loss
        
        return {
            'head_loss': head_loss,
            'power_loss': power_loss,
            'loss_coefficient': loss_coefficient,
            'loss_type': loss_type
        }

# ====================== نظام التصميم المتكامل ======================

class AdvancedChannelDesigner:
    """
    النظام المتكامل لتصميم وتحليل القنوات المفتوحة
    """
    
    def __init__(self):
        self.theories = HydraulicTheories()
        self.g = 9.81
        
        # قاعدة بيانات معاملات مانينج الموسعة
        self.manning_database = {
            'concrete_smooth': 0.012,
            'concrete_rough': 0.015,
            'earth_straight': 0.022,
            'earth_winding': 0.030,
            'rock_excavated': 0.035,
            'gravel_bottom': 0.028,
            'vegetated': 0.050,
            'riprap': 0.030,
            'steel': 0.012,
            'plastic': 0.009
        }
        
        # سجل المشاريع
        self.projects = {}
    
    def create_channel(self, channel_type: str, **kwargs) -> ChannelGeometry:
        """
        إنشاء قناة جديدة بنوع محدد
        
        Parameters:
        -----------
        channel_type : نوع القناة
        **kwargs : المعاملات الهندسية
        
        Returns:
        --------
        ChannelGeometry : هندسة القناة
        """
        type_mapping = {
            'rectangular': ChannelType.RECTANGULAR,
            'trapezoidal': ChannelType.TRAPEZOIDAL,
            'triangular': ChannelType.TRIANGULAR,
            'circular': ChannelType.CIRCULAR,
            'parabolic': ChannelType.PARABOLIC
        }
        
        channel_enum = type_mapping.get(channel_type.lower(), ChannelType.TRAPEZOIDAL)
        
        geometry = ChannelGeometry(
            channel_type=channel_enum,
            bottom_width=kwargs.get('bottom_width', 1.0),
            side_slope=kwargs.get('side_slope', 1.0),
            diameter=kwargs.get('diameter', 1.0),
            depth=kwargs.get('depth', 1.0)
        )
        
        return geometry
    
    def design_optimal_section(self, Q: float, n: float, S: float,
                              channel_type: ChannelType = ChannelType.TRAPEZOIDAL,
                              constraint: str = 'hydraulic_efficiency') -> Dict:
        """
        تصميم المقطع الأمثل للقناة
        
        Parameters:
        -----------
        Q : التصريف المطلوب
        n : معامل مانينج
        S : ميل القاع
        channel_type : نوع المقطع
        constraint : معيار التحسين
        
        Returns:
        --------
        Dict : أبعاد المقطع الأمثل
        """
        if channel_type == ChannelType.TRAPEZOIDAL:
            # النسبة المثلى للمقطع شبه المنحرف
            def optimal_trapezoidal(z):
                """حساب النسبة المثلى للعرض إلى العمق"""
                # أفضل مقطع هيدروليكي: نصف سداسي
                b_y_ratio = 2 * (np.sqrt(1 + z**2) - z)
                return b_y_ratio
            
            # البحث عن أفضل ميل جانبي
            best_solution = None
            min_area = float('inf')
            
            for z in np.linspace(0.5, 2.5, 20):
                b_y = optimal_trapezoidal(z)
                
                # حساب العمق المطلوب
                def area_function(y):
                    b = b_y * y
                    A = b * y + z * y**2
                    P = b + 2 * y * np.sqrt(1 + z**2)
                    R = A / P
                    return (1/n) * A * R**(2/3) * np.sqrt(S) - Q
                
                try:
                    y_solution = root_scalar(area_function, 
                                           bracket=[0.1, 10.0],
                                           method='bisect').root
                    
                    b = b_y * y_solution
                    A = b * y_solution + z * y_solution**2
                    
                    if A < min_area:
                        min_area = A
                        best_solution = {
                            'bottom_width': b,
                            'depth': y_solution,
                            'side_slope': z,
                            'area': A,
                            'velocity': Q / A,
                            'width_depth_ratio': b_y
                        }
                except:
                    continue
            
            if best_solution:
                return best_solution
        
        elif channel_type == ChannelType.RECTANGULAR:
            # أفضل مقطع مستطيل: b = 2y
            def rect_function(y):
                b = 2 * y
                A = b * y
                P = b + 2 * y
                R = A / P
                return (1/n) * A * R**(2/3) * np.sqrt(S) - Q
            
            y_opt = root_scalar(rect_function, 
                               bracket=[0.1, 10.0],
                               method='bisect').root
            b_opt = 2 * y_opt
            
            return {
                'bottom_width': b_opt,
                'depth': y_opt,
                'area': b_opt * y_opt,
                'velocity': Q / (b_opt * y_opt),
                'width_depth_ratio': 2.0
            }
        
        return {}
    
    def comprehensive_flow_analysis(self, geometry: ChannelGeometry,
                                   Q: float, n: float, S: float,
                                   analysis_types: List[str] = None) -> Dict:
        """
        تحليل تدفق شامل باستخدام جميع النظريات
        
        Parameters:
        -----------
        geometry : هندسة القناة
        Q : التصريف
        n : معامل مانينج
        S : ميل القاع
        analysis_types : أنواع التحليلات المطلوبة
        
        Returns:
        --------
        Dict : نتائج التحليل الشامل
        """
        if analysis_types is None:
            analysis_types = ['uniform', 'critical', 'energy', 'gvf']
        
        results = {
            'geometry': geometry,
            'input_parameters': {'Q': Q, 'n': n, 'S': S}
        }
        
        # 1. تحليل التدفق المنتظم (مانينج)
        if 'uniform' in analysis_types:
            yn = self.theories.normal_depth_calculation(geometry, Q, n, S)
            manning_results = self.theories.manning_equation(geometry, n, S, yn)
            results['uniform_flow'] = {
                'normal_depth': yn,
                'manning_results': manning_results,
                'flow_regime': self.theories.classify_flow(manning_results['froude_number'])
            }
        
        # 2. تحليل التدفق الحرج
        if 'critical' in analysis_types:
            critical_results = self.theories.critical_flow_analysis(geometry, Q)
            results['critical_flow'] = critical_results
        
        # 3. تحليل الطاقة
        if 'energy' in analysis_types:
            if 'uniform_flow' in results:
                V = results['uniform_flow']['manning_results']['velocity']
                y = results['uniform_flow']['normal_depth']
                
                E = y + V**2/(2*self.g)
                results['energy_analysis'] = {
                    'specific_energy': E,
                    'potential_energy': y,
                    'kinetic_energy': V**2/(2*self.g),
                    'total_head': E + 100  # بافتراض منسوب مرجعي 100م
                }
        
        # 4. تحليل التدفق المتغير تدريجياً
        if 'gvf' in analysis_types:
            if 'uniform_flow' in results:
                y_start = results['uniform_flow']['normal_depth']
                L = 100  # طول افتراضي 100م
                
                gvf_results = self.theories.gradually_varied_flow(
                    geometry, Q, n, S, y_start * 1.2, L
                )
                results['gvf_analysis'] = gvf_results
        
        return results
    
    def stability_analysis(self, geometry: ChannelGeometry,
                          Q: float, soil_properties: Dict) -> Dict:
        """
        تحليل استقرار القناة
        
        Parameters:
        -----------
        geometry : هندسة القناة
        Q : التصريف
        soil_properties : خصائص التربة
        
        Returns:
        --------
        Dict : نتائج تحليل الاستقرار
        """
        results = {}
        
        # خصائص التربة
        phi = soil_properties.get('friction_angle', 30)  # زاوية الاحتكاك
        c = soil_properties.get('cohesion', 0)  # التماسك (كيلو باسكال)
        gamma = soil_properties.get('unit_weight', 18)  # وزن الوحدة (كيلو نيوتن/م³)
        
        # 1. استقرار الجوانب
        z = geometry.side_slope
        y = geometry.depth
        
        # عامل الأمان للانزلاق
        FS_sliding = (c + gamma * y * np.cos(np.arctan(1/z)) * np.tan(np.radians(phi))) / \
                     (gamma * y * np.sin(np.arctan(1/z)))
        
        results['slope_stability'] = {
            'factor_of_safety': FS_sliding,
            'stable': FS_sliding > 1.5,
            'critical_slope': 1/np.tan(np.radians(phi))
        }
        
        # 2. تحليل التآكل
        V = Q / geometry.area()
        
        # السرعة المسموحة حسب نوع التربة
        permissible_velocities = {
            'fine_sand': 0.45,
            'coarse_sand': 0.60,
            'sandy_loam': 0.75,
            'silt': 0.90,
            'clay': 1.20,
            'gravel': 1.50
        }
        
        soil_type = soil_properties.get('type', 'sandy_loam')
        V_allowable = permissible_velocities.get(soil_type, 0.75)
        
        results['erosion_analysis'] = {
            'actual_velocity': V,
            'allowable_velocity': V_allowable,
            'erosion_risk': V > V_allowable,
            'safety_margin': (V_allowable - V) / V_allowable * 100
        }
        
        return results
    
    def generate_comprehensive_report(self, analysis_results: Dict,
                                     filename: str = 'hydraulic_report.txt') -> None:
        """
        إنشاء تقرير شامل باللغة العربية
        
        Parameters:
        -----------
        analysis_results : نتائج التحليل
        filename : اسم ملف التقرير
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 80 + "\n")
            f.write("تقرير التصميم الهيدروليكي المتقدم للقنوات المفتوحة\n")
            f.write("=" * 80 + "\n\n")
            
            # المعطيات الأساسية
            params = analysis_results.get('input_parameters', {})
            f.write("📋 معطيات التصميم:\n")
            f.write("-" * 40 + "\n")
            f.write(f"التصريف: {params.get('Q', 0):.2f} م³/ث\n")
            f.write(f"معامل مانينج: {params.get('n', 0):.3f}\n")
            f.write(f"ميل القاع: {params.get('S', 0):.4f}\n\n")
            
            # نتائج التدفق المنتظم
            if 'uniform_flow' in analysis_results:
                uf = analysis_results['uniform_flow']
                f.write("📊 تحليل التدفق المنتظم (معادلة مانينج):\n")
                f.write("-" * 40 + "\n")
                f.write(f"العمق الطبيعي: {uf['normal_depth']:.3f} م\n")
                
                mr = uf['manning_results']
                f.write(f"السرعة: {mr['velocity']:.3f} م/ث\n")
                f.write(f"رقم فرود: {mr['froude_number']:.3f}\n")
                f.write(f"نظام التدفق: {uf['flow_regime'].value}\n\n")
            
            # نتائج التدفق الحرج
            if 'critical_flow' in analysis_results:
                cf = analysis_results['critical_flow']
                f.write("📊 تحليل التدفق الحرج:\n")
                f.write("-" * 40 + "\n")
                f.write(f"العمق الحرج: {cf['critical_depth']:.3f} م\n")
                f.write(f"السرعة الحرجة: {cf['critical_velocity']:.3f} م/ث\n")
                f.write(f"الطاقة النوعية الصغرى: {cf['specific_energy_min']:.3f} م\n\n")
            
            # نتائج تحليل الطاقة
            if 'energy_analysis' in analysis_results:
                ea = analysis_results['energy_analysis']
                f.write("📊 تحليل الطاقة:\n")
                f.write("-" * 40 + "\n")
                f.write(f"الطاقة النوعية: {ea['specific_energy']:.3f} م\n")
                f.write(f"طاقة الوضع: {ea['potential_energy']:.3f} م\n")
                f.write(f"طاقة الحركة: {ea['kinetic_energy']:.3f} م\n\n")
            
            f.write("=" * 80 + "\n")
            f.write("تم إنشاء التقرير بواسطة نظام التصميم الهيدروليكي المتقدم\n")
        
        print(f"✓ تم حفظ التقرير في: {filename}")
    
    def plot_comprehensive_results(self, analysis_results: Dict,
                                  save_fig: bool = True) -> None:
        """
        رسم النتائج الشاملة بيانياً
        
        Parameters:
        -----------
        analysis_results : نتائج التحليل
        save_fig : حفظ الشكل
        """
        fig = plt.figure(figsize=(16, 12))
        
        # 1. المقطع العرضي للقناة
        ax1 = plt.subplot(2, 3, 1)
        geometry = analysis_results['geometry']
        
        if geometry.channel_type == ChannelType.TRAPEZOIDAL:
            b = geometry.bottom_width
            y = geometry.depth
            z = geometry.side_slope
            
            # نقاط المقطع
            x_points = [-z*y, 0, b, b + z*y]
            y_points = [y, 0, 0, y]
            
            ax1.fill(x_points, y_points, alpha=0.3, color='blue')
            ax1.plot(x_points, y_points, 'b-', linewidth=2)
            ax1.axhline(y=0, color='black', linewidth=1)
            
            # مستوى الماء
            ax1.axhline(y=y, color='blue', linestyle='--', alpha=0.5)
            ax1.fill_between([-z*y, b + z*y], [y, y], [0, 0], alpha=0.1, color='blue')
            
            ax1.set_title('المقطع العرضي للقناة')
            ax1.set_xlabel('العرض (م)')
            ax1.set_ylabel('العمق (م)')
            ax1.grid(True, alpha=0.3)
            ax1.set_aspect('equal')
        
        # 2. منحنيات التصريف
        ax2 = plt.subplot(2, 3, 2)
        depths = np.linspace(0.1, 3.0, 50)
        discharges = []
        
        Q_design = analysis_results['input_parameters']['Q']
        n = analysis_results['input_parameters']['n']
        S = analysis_results['input_parameters']['S']
        
        for y in depths:
            try:
                Q_calc = self.theories.manning_equation(geometry, n, S, y)['discharge']
                discharges.append(Q_calc)
            except:
                discharges.append(0)
        
        ax2.plot(depths, discharges, 'b-', linewidth=2)
        ax2.axhline(y=Q_design, color='red', linestyle='--', 
                   label=f'التصريف المطلوب = {Q_design:.2f} م³/ث')
        
        if 'uniform_flow' in analysis_results:
            yn = analysis_results['uniform_flow']['normal_depth']
            ax2.axvline(x=yn, color='green', linestyle='--', 
                       label=f'العمق الطبيعي = {yn:.3f} م')
        
        ax2.set_xlabel('عمق المياه (م)')
        ax2.set_ylabel('التصريف (م³/ث)')
        ax2.set_title('منحنى التصريف')
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. منحنى الطاقة النوعية
        ax3 = plt.subplot(2, 3, 3)
        
        if 'uniform_flow' in analysis_results:
            yn = analysis_results['uniform_flow']['normal_depth']
            y_range = np.linspace(0.5*yn, 2*yn, 100)
            
            Q = analysis_results['input_parameters']['Q']
            energies = []
            
            for y in y_range:
                A = geometry.area(y)
                V = Q / A
                E = y + V**2/(2*self.g)
                energies.append(E)
            
            ax3.plot(energies, y_range, 'b-', linewidth=2)
            
            # نقطة الطاقة الصغرى (العمق الحرج)
            if 'critical_flow' in analysis_results:
                yc = analysis_results['critical_flow']['critical_depth']
                Ec = analysis_results['critical_flow']['specific_energy_min']
                ax3.plot(Ec, yc, 'ro', markersize=10, label=f'حرج yc={yc:.3f}م')
            
            ax3.plot(yn + (Q/geometry.area(yn))**2/(2*self.g), yn, 
                    'go', markersize=10, label=f'طبيعي yn={yn:.3f}م')
            
            ax3.set_xlabel('الطاقة النوعية (م)')
            ax3.set_ylabel('عمق المياه (م)')
            ax3.set_title('منحنى الطاقة النوعية')
            ax3.legend()
            ax3.grid(True, alpha=0.3)
        
        # 4. ملامح سطح الماء للتدفق المتغير
        if 'gvf_analysis' in analysis_results:
            ax4 = plt.subplot(2, 3, 4)
            gvf = analysis_results['gvf_analysis']
            
            x = gvf['distance']
            water_surface = gvf['water_surface']
            bed = gvf['bed_elevation']
            
            # سطح الماء
            ax4.fill_between(x, bed, water_surface + bed, 
                            alpha=0.3, color='blue')
            ax4.plot(x, water_surface + bed, 'b-', linewidth=2, 
                    label='سطح الماء')
            ax4.plot(x, bed, 'brown', linewidth=2, label='قاع القناة')
            
            # خطوط العمق الحرج والطبيعي
            ax4.axhline(y=gvf['normal_depth'], color='green', 
                       linestyle='--', label='العمق الطبيعي')
            ax4.axhline(y=gvf['critical_depth'], color='red', 
                       linestyle='--', label='العمق الحرج')
            
            ax4.set_xlabel('المسافة (م)')
            ax4.set_ylabel('المنسوب (م)')
            ax4.set_title(f'ملف سطح الماء - {gvf["curve_type"]}')
            ax4.legend()
            ax4.grid(True, alpha=0.3)
        
        # 5. توزيع رقم فرود
        if 'gvf_analysis' in analysis_results:
            ax5 = plt.subplot(2, 3, 5)
            gvf = analysis_results['gvf_analysis']
            
            ax5.plot(gvf['distance'], gvf['froude_profile'], 
                    'b-', linewidth=2)
            ax5.axhline(y=1.0, color='red', linestyle='--', 
                       label='الحد الحرج')
            
            ax5.set_xlabel('المسافة (م)')
            ax5.set_ylabel('رقم فرود')
            ax5.set_title('توزيع رقم فرود')
            ax5.legend()
            ax5.grid(True, alpha=0.3)
        
        # 6. مقارنة النظريات
        ax6 = plt.subplot(2, 3, 6)
        
        theories = ['مانينج', 'تشيز', 'برنولي']
        velocities = []
        
        if 'uniform_flow' in analysis_results:
            velocities.append(
                analysis_results['uniform_flow']['manning_results']['velocity']
            )
        
        # تشيز
        C = 50  # معامل تشيز افتراضي
        chezy_results = self.theories.chezy_equation(geometry, C, S)
        velocities.append(chezy_results['velocity'])
        
        # برنولي (تقدير)
        if len(velocities) > 0:
            velocities.append(velocities[0] * 0.95)
        
        bars = ax6.bar(theories, velocities, 
                      color=['steelblue', 'coral', 'lightgreen'])
        ax6.set_ylabel('السرعة (م/ث)')
        ax6.set_title('مقارنة السرعات حسب النظريات المختلفة')
        
        # إضافة القيم فوق الأعمدة
        for bar, v in zip(bars, velocities):
            ax6.text(bar.get_x() + bar.get_width()/2., bar.get_height(),
                    f'{v:.3f}', ha='center', va='bottom')
        
        ax6.grid(True, alpha=0.3)
        
        plt.suptitle('التحليل الهيدروليكي المتقدم للقناة', fontsize=16, y=1.02)
        plt.tight_layout()
        
        if save_fig:
            plt.savefig('hydraulic_analysis.png', dpi=150, bbox_inches='tight')
        
        plt.show()

# ====================== واجهة الاستخدام ======================

def main_interactive():
    """
    واجهة تفاعلية متقدمة لتصميم القنوات
    """
    print("\n" + "=" * 80)
    print("نظام التصميم الهيدروليكي المتقدم للقنوات المفتوحة")
    print("=" * 80)
    
    designer = AdvancedChannelDesigner()
    
    # إدخال المعطيات الأساسية
    print("\n📋 إدخال معطيات التصميم:")
    print("-" * 40)
    
    Q = float(input("التصريف المطلوب (م³/ث): ") or "10.0")
    
    print("\nاختر نوع القناة:")
    types = ["مستطيل", "شبه منحرف", "مثلث", "دائري", "مكافئي"]
    for i, t in enumerate(types, 1):
        print(f"{i}. {t}")
    
    choice = int(input("الاختيار (1-5): ") or "2")
    type_mapping = {
        1: 'rectangular', 2: 'trapezoidal', 3: 'triangular',
        4: 'circular', 5: 'parabolic'
    }
    
    channel_type = type_mapping[choice]
    
    print("\nاختر نوع سطح القناة:")
    surfaces = list(designer.manning_database.keys())
    for i, s in enumerate(surfaces, 1):
        print(f"{i}. {s}")
    
    surface_choice = int(input("الاختيار: ") or "3")
    n = designer.manning_database[surfaces[surface_choice-1]]
    
    S = float(input("ميل القاع (م/م): ") or "0.001")
    
    # إنشاء القناة وتصميمها
    geometry = designer.create_channel(
        channel_type,
        bottom_width=float(input("عرض القاع (م) [اختياري]: ") or "0"),
        side_slope=float(input("الميل الجانبي [اختياري]: ") or "1.0")
    )
    
    # التصميم الأمثل
    print("\n🔄 جاري التصميم الأمثل...")
    optimal = designer.design_optimal_section(Q, n, S, geometry.channel_type)
    
    if optimal:
        print("\n📐 أبعاد المقطع الأمثل:")
        print(f"  عرض القاع: {optimal.get('bottom_width', 0):.3f} م")
        print(f"  عمق المياه: {optimal.get('depth', 0):.3f} م")
        print(f"  المساحة: {optimal.get('area', 0):.3f} م²")
        print(f"  السرعة: {optimal.get('velocity', 0):.3f} م/ث")
        
        # تحديث هندسة القناة
        geometry.bottom_width = optimal['bottom_width']
        geometry.depth = optimal['depth']
        geometry.side_slope = optimal.get('side_slope', geometry.side_slope)
    
    # التحليل الشامل
    print("\n🔍 جاري التحليل الشامل...")
    analysis_results = designer.comprehensive_flow_analysis(
        geometry, Q, n, S,
        analysis_types=['uniform', 'critical', 'energy', 'gvf']
    )
    
    # تحليل الاستقرار
    soil_props = {
        'type': 'sandy_loam',
        'friction_angle': 30,
        'cohesion': 5,
        'unit_weight': 18
    }
    
    stability = designer.stability_analysis(geometry, Q, soil_props)
    analysis_results['stability'] = stability
    
    # عرض النتائج
    designer.generate_comprehensive_report(analysis_results)
    designer.plot_comprehensive_results(analysis_results)
    
    return analysis_results

# ====================== أمثلة تطبيقية ======================

def example_applications():
    """
    أمثلة تطبيقية متنوعة
    """
    designer = AdvancedChannelDesigner()
    
    print("\n" + "🏗️ " * 30)
    print("أمثلة تطبيقية للتصميم الهيدروليكي المتقدم")
    print("🏗️ " * 30)
    
    # مثال 1: قناة شبه منحرفة
    print("\n📌 المثال 1: تصميم قناة ري شبه منحرفة")
    print("-" * 50)
    
    geometry1 = designer.create_channel(
        'trapezoidal',
        bottom_width=2.0,
        side_slope=1.5,
        depth=1.5
    )
    
    analysis1 = designer.comprehensive_flow_analysis(
        geometry1, Q=5.0, n=0.025, S=0.0005
    )
    
    print(f"العمق الطبيعي: {analysis1['uniform_flow']['normal_depth']:.3f} م")
    print(f"السرعة: {analysis1['uniform_flow']['manning_results']['velocity']:.3f} م/ث")
    print(f"رقم فرود: {analysis1['uniform_flow']['manning_results']['froude_number']:.3f}")
    
    # مثال 2: قناة دائرية
    print("\n📌 المثال 2: تحليل قناة تصريف دائرية")
    print("-" * 50)
    
    geometry2 = designer.create_channel(
        'circular',
        diameter=2.0
    )
    
    analysis2 = designer.comprehensive_flow_analysis(
        geometry2, Q=3.0, n=0.013, S=0.001,
        analysis_types=['uniform', 'critical']
    )
    
    print(f"العمق الطبيعي: {analysis2['uniform_flow']['normal_depth']:.3f} م")
    print(f"العمق الحرج: {analysis2['critical_flow']['critical_depth']:.3f} م")
    
    # مثال 3: تحليل التدفق المتغير
    print("\n📌 المثال 3: تحليل التدفق المتغير تدريجياً")
    print("-" * 50)
    
    geometry3 = designer.create_channel(
        'rectangular',
        bottom_width=3.0,
        depth=2.0
    )
    
    analysis3 = designer.comprehensive_flow_analysis(
        geometry3, Q=15.0, n=0.030, S=0.002,
        analysis_types=['uniform', 'critical', 'gvf']
    )
    
    if 'gvf_analysis' in analysis3:
        print(f"نوع المنحنى: {analysis3['gvf_analysis']['curve_type']}")
    
    # عرض النتائج بيانياً
    designer.plot_comprehensive_results(analysis3)

# ====================== تشغيل البرنامج ======================

if __name__ == "__main__":
    # تشغيل الأمثلة التطبيقية
    example_applications()
    
    # أو تشغيل الواجهة التفاعلية
    # main_interactive()