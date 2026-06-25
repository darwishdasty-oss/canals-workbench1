"""
نظام تصميم القنوات الترابية باستخدام نظريات لاسي وكينيدي
Earth Canal Design System using Lacey and Kennedy Theories
===========================================================
المؤلف: خبير هندسة الموارد المائية
التاريخ: 2024
الإصدار: 1.0
"""

import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve, minimize_scalar
from scipy.interpolate import interp1d
from typing import Dict, List, Tuple, Optional
import warnings
warnings.filterwarnings('ignore')

# ====================== الإعدادات العربية ======================
plt.rcParams['font.family'] = 'DejaVu Sans'
plt.rcParams['font.size'] = 12

class EarthCanalDesigner:
    """
    الفئة الرئيسية لتصميم القنوات الترابية باستخدام نظريات متعددة
    """
    
    def __init__(self):
        """
        تهيئة المصمم مع إعداد القيم الافتراضية والمعاملات
        """
        self.g = 9.81  # تسارع الجاذبية (م/ث²)
        self.results = {}
        self.theory_comparison = {}
        
        # معاملات مانينج للقنوات الترابية
        self.manning_n = {
            'smooth_earth': 0.017,
            'ordinary_earth': 0.025,
            'rough_earth': 0.030,
            'gravelly_earth': 0.025,
            'sandy_earth': 0.027
        }
        
        # معاملات التربة حسب تصنيف لاسي
        self.lacey_silt_factors = {
            'very_fine_silt': 0.4,
            'fine_silt': 0.6,
            'medium_silt': 0.8,
            'coarse_silt': 1.0,
            'fine_sand': 1.2,
            'medium_sand': 1.5,
            'coarse_sand': 2.0,
            'gravel': 2.5
        }
        
    def lacey_theory_design(self, Q: float, f: float, side_slope: float = 0.5) -> Dict:
        """
        تصميم القناة باستخدام نظرية لاسي
        
        المعاملات:
        ----------
        Q : float
            معدل التصريف (م³/ث)
        f : float
            عامل الطمي للاسي (حسب نوع التربة)
        side_slope : float
            الميل الجانبي (أفقي:عمودي)، افتراضي = 0.5
            
        المخرجات:
        --------
        Dict: قاموس يحتوي على أبعاد القناة ومؤشرات الاستقرار
        """
        
        def calculate_lacey_parameters(Q, f):
            """
            حساب المعاملات الأساسية لنظرية لاسي
            """
            # السرعة الحرجة (معادلة لاسي الأساسية)
            V = 0.4382 * (Q * f**2 / 140)**(1/6)  # م/ث
            
            # المساحة المقطعية
            A = Q / V  # م²
            
            # المحيط المبلل (معادلة لاسي)
            P = 4.75 * np.sqrt(Q)  # م
            
            # نصف القطر الهيدروليكي
            R = A / P  # م
            
            # عرض القاعدة (حل المعادلة التربيعية)
            # A = B*y + z*y²
            # P = B + 2*y*sqrt(1+z²)
            # حيث z = side_slope
            
            z = side_slope
            k = 2 * np.sqrt(1 + z**2)
            
            # حل لإيجاد y (عمق المياه)
            def equation_for_y(y):
                B = (A - z * y**2) / y
                P_calc = B + k * y
                return P_calc - P
            
            # استخدام fsolve لحل المعادلة
            y_initial_guess = np.sqrt(A / (2 + z))  # تخمين مبدئي
            y_solution = fsolve(equation_for_y, y_initial_guess)[0]
            
            # حساب عرض القاعدة
            B = (A - z * y_solution**2) / y_solution
            
            # التحقق من الاستقرار
            S = (f**(5/3)) / (3340 * Q**(1/6))  # ميل القاع
            
            return {
                'velocity': V,
                'area': A,
                'wetted_perimeter': P,
                'hydraulic_radius': R,
                'depth': y_solution,
                'bed_width': B,
                'bed_slope': S,
                'froude_number': V / np.sqrt(self.g * y_solution)
            }
        
        params = calculate_lacey_parameters(Q, f)
        
        # التحقق من معايير الاستقرار
        stability_checks = {
            'velocity_check': 0.6 <= params['velocity'] <= 0.9,  # نطاق السرعة المسموح
            'froude_check': params['froude_number'] < 0.8,  # تدفق دون الحرج
            'width_depth_ratio': 2 <= params['bed_width']/params['depth'] <= 8,
            'hydraulic_radius_check': params['hydraulic_radius'] > 0.3
        }
        
        params['stability_status'] = all(stability_checks.values())
        params['stability_details'] = stability_checks
        
        return params
    
    def kennedy_theory_design(self, Q: float, n: float, S: float, 
                            side_slope: float = 0.5, CVR: float = 1.0) -> Dict:
        """
        تصميم القناة باستخدام نظرية كينيدي
        
        المعاملات:
        ----------
        Q : float
            معدل التصريف (م³/ث)
        n : float
            معامل مانينج للخشونة
        S : float
            ميل القاع (م/م)
        side_slope : float
            الميل الجانبي
        CVR : float
            النسبة الحرجة للسرعة (Critical Velocity Ratio)
            
        المخرجات:
        --------
        Dict: قاموس يحتوي على أبعاد القناة ومؤشرات الاستقرار
        """
        
        def kennedy_velocity(y, B, z):
            """
            حساب السرعة الحرجة حسب معادلة كينيدي
            """
            A = B * y + z * y**2
            V_critical = 0.55 * CVR * y**0.64
            return V_critical
        
        def optimize_section(Q, n, S, z):
            """
            تحسين المقطع العرضي للقناة
            """
            
            def objective(params):
                B, y = params
                
                if B <= 0 or y <= 0:
                    return 1e10
                
                # حساب المعاملات الهيدروليكية
                A = B * y + z * y**2
                P = B + 2 * y * np.sqrt(1 + z**2)
                R = A / P
                
                # حساب السرعة باستخدام مانينج
                V_manning = (1/n) * R**(2/3) * np.sqrt(S)
                Q_calc = A * V_manning
                
                # السرعة الحرجة حسب كينيدي
                V_critical = kennedy_velocity(y, B, z)
                
                # دالة الهدف: تقليل الفرق بين التصريف المطلوب والمحسوب
                error_Q = (Q_calc - Q)**2
                
                # مع عقوبة للفرق بين السرعات
                error_V = (V_manning - V_critical)**2
                
                return error_Q + 0.1 * error_V
            
            # القيود والحدود
            from scipy.optimize import minimize
            
            # تخمين مبدئي
            initial_guess = [np.sqrt(Q), np.sqrt(Q/2)]
            bounds = [(0.5, 20), (0.1, 5)]
            
            result = minimize(objective, initial_guess, 
                            method='L-BFGS-B', 
                            bounds=bounds)
            
            return result.x[0], result.x[1]  # B, y
        
        # تحسين أبعاد القناة
        B_opt, y_opt = optimize_section(Q, n, S, side_slope)
        
        # حساب المعاملات النهائية
        A = B_opt * y_opt + side_slope * y_opt**2
        P = B_opt + 2 * y_opt * np.sqrt(1 + side_slope**2)
        R = A / P
        V = Q / A
        V_critical = kennedy_velocity(y_opt, B_opt, side_slope)
        
        params = {
            'bed_width': B_opt,
            'depth': y_opt,
            'area': A,
            'wetted_perimeter': P,
            'hydraulic_radius': R,
            'velocity': V,
            'critical_velocity': V_critical,
            'velocity_ratio': V / V_critical,
            'froude_number': V / np.sqrt(self.g * y_opt)
        }
        
        # التحقق من معايير كينيدي
        stability_checks = {
            'velocity_ratio_check': 0.9 <= params['velocity_ratio'] <= 1.1,
            'froude_check': params['froude_number'] < 1.0,
            'depth_check': y_opt > 0.3,
            'width_depth_ratio': 2 <= B_opt/y_opt <= 10
        }
        
        params['stability_status'] = all(stability_checks.values())
        params['stability_details'] = stability_checks
        
        return params
    
    def manning_design(self, Q: float, n: float, S: float, 
                      side_slope: float = 1.0) -> Dict:
        """
        تصميم إضافي باستخدام معادلة مانينج (للأغراض المقارنة)
        """
        def solve_manning(y, Q, n, S, z):
            B = (Q * n / (np.sqrt(S) * (B * y + z * y**2) * 
                 (y/(B + 2*y*np.sqrt(1+z**2)))**(2/3))) - 1
            return B
        
        # البحث عن أفضل الأبعاد
        best_solution = None
        min_cost = float('inf')
        
        y_range = np.linspace(0.5, 3.0, 50)
        
        for y in y_range:
            try:
                B = fsolve(lambda B: (B*y + side_slope*y**2) * 
                          (1/0.025) * ((B*y + side_slope*y**2)/
                          (B + 2*y*np.sqrt(1+side_slope**2)))**(2/3) * 
                          np.sqrt(S) - Q, 2.0)[0]
                
                if B > 0:
                    # حساب تكلفة الحفر التقريبية
                    area = B*y + side_slope*y**2
                    excavation = area * 1.0  # لكل متر طول
                    
                    if excavation < min_cost:
                        min_cost = excavation
                        best_solution = (B, y)
                        
            except:
                continue
        
        if best_solution:
            B_opt, y_opt = best_solution
            A = B_opt * y_opt + side_slope * y_opt**2
            P = B_opt + 2 * y_opt * np.sqrt(1 + side_slope**2)
            R = A / P
            V = Q / A
            
            return {
                'bed_width': B_opt,
                'depth': y_opt,
                'area': A,
                'wetted_perimeter': P,
                'hydraulic_radius': R,
                'velocity': V,
                'froude_number': V / np.sqrt(self.g * y_opt)
            }
    
    def comprehensive_analysis(self, Q: float, soil_type: str = 'medium_silt',
                             manning_n: float = 0.025, bed_slope: float = None,
                             side_slope: float = 0.5) -> Dict:
        """
        تحليل شامل باستخدام جميع النظريات المتاحة
        
        المعاملات:
        ----------
        Q : float
            معدل التصريف
        soil_type : str
            نوع التربة حسب تصنيف لاسي
        manning_n : float
            معامل مانينج
        bed_slope : float
            ميل القاع (إذا كان معروفاً)
        side_slope : float
            الميل الجانبي
        """
        
        # الحصول على عامل الطمي
        f = self.lacey_silt_factors.get(soil_type, 0.8)
        
        # إذا لم يتم تحديد الميل، استخدام قيمة افتراضية
        if bed_slope is None:
            bed_slope = 0.0001  # ميل افتراضي للقنوات الترابية
        
        print("=" * 70)
        print("تحليل شامل لتصميم القناة الترابية")
        print("=" * 70)
        print(f"التصريف: {Q:.2f} م³/ث")
        print(f"نوع التربة: {soil_type} (عامل لاسي: {f})")
        print("=" * 70)
        
        # تطبيق نظرية لاسي
        print("\n📊 نتائج نظرية لاسي:")
        print("-" * 40)
        lacey_results = self.lacey_theory_design(Q, f, side_slope)
        self._print_design_results(lacey_results, "لاسي")
        
        # تطبيق نظرية كينيدي
        print("\n📊 نتائج نظرية كينيدي:")
        print("-" * 40)
        kennedy_results = self.kennedy_theory_design(Q, manning_n, bed_slope, side_slope)
        self._print_design_results(kennedy_results, "كينيدي")
        
        # تجميع النتائج
        self.results = {
            'lacey': lacey_results,
            'kennedy': kennedy_results,
            'input_parameters': {
                'Q': Q,
                'soil_type': soil_type,
                'lacey_factor': f,
                'manning_n': manning_n,
                'bed_slope': bed_slope,
                'side_slope': side_slope
            }
        }
        
        # إنشاء الرسوم البيانية
        self._create_comparison_plots()
        
        return self.results
    
    def _print_design_results(self, results: Dict, theory_name: str):
        """
        طباعة نتائج التصميم بشكل منسق
        """
        print(f"✓ عرض القاعدة: {results.get('bed_width', 0):.3f} م")
        print(f"✓ عمق المياه: {results.get('depth', 0):.3f} م")
        print(f"✓ المساحة المقطعية: {results.get('area', 0):.3f} م²")
        print(f"✓ السرعة: {results.get('velocity', 0):.3f} م/ث")
        print(f"✓ رقم فرود: {results.get('froude_number', 0):.3f}")
        
        if 'stability_status' in results:
            status = "مستقر ✓" if results['stability_status'] else "غير مستقر ⚠"
            print(f"✓ حالة الاستقرار: {status}")
    
    def _create_comparison_plots(self):
        """
        إنشاء رسوم بيانية للمقارنة بين النظريات
        """
        fig, axes = plt.subplots(2, 2, figsize=(14, 10))
        
        # مقارنة الأبعاد
        theories = list(self.results.keys())
        theories = [t for t in theories if t != 'input_parameters']
        
        bed_widths = [self.results[t].get('bed_width', 0) for t in theories]
        depths = [self.results[t].get('depth', 0) for t in theories]
        
        x = np.arange(len(theories))
        width = 0.35
        
        axes[0, 0].bar(x - width/2, bed_widths, width, label='عرض القاعدة', color='steelblue')
        axes[0, 0].bar(x + width/2, depths, width, label='عمق المياه', color='coral')
        axes[0, 0].set_xlabel('النظرية')
        axes[0, 0].set_ylabel('الأبعاد (م)')
        axes[0, 0].set_title('مقارنة أبعاد القناة')
        axes[0, 0].set_xticks(x)
        axes[0, 0].set_xticklabels(theories)
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # مقارنة السرعات
        velocities = [self.results[t].get('velocity', 0) for t in theories]
        axes[0, 1].bar(theories, velocities, color=['steelblue', 'coral'])
        axes[0, 1].set_ylabel('السرعة (م/ث)')
        axes[0, 1].set_title('مقارنة السرعات')
        axes[0, 1].grid(True, alpha=0.3)
        
        # مقارنة أرقام فرود
        froude_numbers = [self.results[t].get('froude_number', 0) for t in theories]
        colors = ['green' if fn < 1 else 'red' for fn in froude_numbers]
        axes[1, 0].bar(theories, froude_numbers, color=colors)
        axes[1, 0].axhline(y=1.0, color='red', linestyle='--', alpha=0.7, label='الحد الحرج')
        axes[1, 0].set_ylabel('رقم فرود')
        axes[1, 0].set_title('مقارنة رقم فرود')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # رسم تخطيطي للمقطع العرضي
        ax = axes[1, 1]
        lacey_results = self.results.get('lacey', {})
        if lacey_results:
            B = lacey_results.get('bed_width', 0)
            y = lacey_results.get('depth', 0)
            z = self.results['input_parameters']['side_slope']
            
            # رسم المقطع العرضي
            x_vals = [0, B, B + z*y, B + z*y + z*1.5, 0, -z*1.5]
            y_vals = [0, 0, -y, -y-1.5, -y-1.5, -y-1.5]
            
            # رسم القناة
            ax.fill_between([0, B], [0, 0], [-y, -y], alpha=0.3, color='blue')
            ax.fill_between([-z*1.5, 0], [-y-1.5, -y-1.5], [-y-1.5, -y-1.5], alpha=0.5, color='brown')
            ax.fill_between([B, B+z*y+z*1.5], [-y, -y-1.5], [-y, -y-1.5], alpha=0.5, color='brown')
            
            # خط الماء
            ax.axhline(y=0, color='blue', linewidth=2, linestyle='-', alpha=0.7)
            
            ax.set_xlim(-2, B+4)
            ax.set_ylim(-y-2, 1)
            ax.set_aspect('equal')
            ax.set_title(f'المقطع العرضي للقناة (نظرية لاسي)\nB={B:.2f}م, y={y:.2f}م')
            ax.grid(True, alpha=0.3)
            
            # إضافة التسميات
            ax.annotate(f'B = {B:.2f} م', xy=(B/2, 0.2), ha='center')
            ax.annotate(f'y = {y:.2f} م', xy=(B+0.3, -y/2), ha='left')
        
        plt.tight_layout()
        plt.savefig('canal_design_comparison.png', dpi=150, bbox_inches='tight')
        plt.show()
    
    def generate_report(self, filename: str = 'canal_design_report.txt'):
        """
        إنشاء تقرير مفصل بنتائج التصميم
        """
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("=" * 70 + "\n")
            f.write("تقرير تصميم القناة الترابية\n")
            f.write("=" * 70 + "\n\n")
            
            # المعطيات
            params = self.results.get('input_parameters', {})
            f.write("📋 معطيات التصميم:\n")
            f.write("-" * 30 + "\n")
            f.write(f"التصريف: {params.get('Q', 0):.2f} م³/ث\n")
            f.write(f"نوع التربة: {params.get('soil_type', 'غير محدد')}\n")
            f.write(f"عامل لاسي: {params.get('lacey_factor', 0)}\n")
            f.write(f"الميل الجانبي: {params.get('side_slope', 0)}\n\n")
            
            # نتائج لاسي
            lacey = self.results.get('lacey', {})
            f.write("📊 نتائج نظرية لاسي:\n")
            f.write("-" * 30 + "\n")
            for key, value in lacey.items():
                if key not in ['stability_details']:
                    f.write(f"  {key}: {value}\n")
            f.write("\n")
            
            # نتائج كينيدي
            kennedy = self.results.get('kennedy', {})
            f.write("📊 نتائج نظرية كينيدي:\n")
            f.write("-" * 30 + "\n")
            for key, value in kennedy.items():
                if key not in ['stability_details']:
                    f.write(f"  {key}: {value}\n")
            
            f.write("\n" + "=" * 70 + "\n")
            f.write("تم إنشاء التقرير بواسطة نظام تصميم القنوات الترابية\n")
        
        print(f"\n✓ تم حفظ التقرير في: {filename}")


# ====================== أمثلة تطبيقية ======================

def example_usage():
    """
    أمثلة على استخدام نظام تصميم القنوات
    """
    # إنشاء كائن من الفئة الرئيسية
    designer = EarthCanalDesigner()
    
    print("\n" + "🏗️ " * 20)
    print("نظام تصميم القنوات الترابية - مثال تطبيقي")
    print("🏗️ " * 20 + "\n")
    
    # الحالة الدراسية 1: قناة صغيرة
    print("\n📌 الحالة الدراسية 1: قناة ري صغيرة")
    designer.comprehensive_analysis(
        Q=5.0,  # تصريف 5 م³/ث
        soil_type='medium_silt',
        manning_n=0.025,
        side_slope=0.5
    )
    designer.generate_report('canal_report_case1.txt')
    
    # الحالة الدراسية 2: قناة رئيسية
    print("\n\n📌 الحالة الدراسية 2: قناة رئيسية")
    designer2 = EarthCanalDesigner()
    designer2.comprehensive_analysis(
        Q=50.0,  # تصريف 50 م³/ث
        soil_type='coarse_silt',
        manning_n=0.025,
        side_slope=1.0
    )
    designer2.generate_report('canal_report_case2.txt')


# ====================== واجهة مستخدم تفاعلية ======================

def interactive_design():
    """
    واجهة تفاعلية لتصميم القنوات
    """
    print("\n" + "=" * 70)
    print("مرحباً بك في نظام تصميم القنوات الترابية التفاعلي")
    print("=" * 70)
    
    designer = EarthCanalDesigner()
    
    while True:
        print("\nاختر نوع التصميم:")
        print("1. تصميم بنظرية لاسي فقط")
        print("2. تصميم بنظرية كينيدي فقط")
        print("3. تحليل شامل (جميع النظريات)")
        print("4. خروج")
        
        choice = input("\nأدخل اختيارك (1-4): ")
        
        if choice == '4':
            print("شكراً لاستخدامك النظام!")
            break
        
        try:
            Q = float(input("أدخل معدل التصريف (م³/ث): "))
            
            if choice == '1':
                soil_type = input("نوع التربة (medium_silt, coarse_silt, fine_sand, etc.): ")
                side_slope = float(input("الميل الجانبي (افتراضي 0.5): ") or "0.5")
                
                f = designer.lacey_silt_factors.get(soil_type, 0.8)
                results = designer.lacey_theory_design(Q, f, side_slope)
                designer._print_design_results(results, "لاسي")
                
            elif choice == '2':
                n = float(input("معامل مانينج (افتراضي 0.025): ") or "0.025")
                S = float(input("ميل القاع (افتراضي 0.0001): ") or "0.0001")
                side_slope = float(input("الميل الجانبي (افتراضي 0.5): ") or "0.5")
                
                results = designer.kennedy_theory_design(Q, n, S, side_slope)
                designer._print_design_results(results, "كينيدي")
                
            elif choice == '3':
                soil_type = input("نوع التربة: ") or "medium_silt"
                n = float(input("معامل مانينج (افتراضي 0.025): ") or "0.025")
                side_slope = float(input("الميل الجانبي (افتراضي 0.5): ") or "0.5")
                
                designer.comprehensive_analysis(Q, soil_type, n, side_slope=side_slope)
                designer.generate_report()
                
        except ValueError as e:
            print(f"خطأ في الإدخال: {e}")
        except Exception as e:
            print(f"حدث خطأ: {e}")


# ====================== تشغيل البرنامج ======================

if __name__ == "__main__":
    # تشغيل المثال التطبيقي
    example_usage()
    
    # أو تشغيل الواجهة التفاعلية (قم بإلغاء التعليق)
    # interactive_design()