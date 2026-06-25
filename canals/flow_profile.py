import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import fsolve, bisect
from scipy.integrate import solve_ivp
import warnings
warnings.filterwarnings('ignore')

class OpenChannelFlow:
    """
    فئة متكاملة لتحليل ورسم منحنيات الجريان في القنوات المفتوحة
    """
    
    def __init__(self):
        self.g = 9.81  # تسارع الجاذبية (م/ث²)
        self.channel_type = None
        self.channel_params = {}
        self.flow_params = {}
        
    def get_user_input(self):
        """
        الحصول على البيانات من المستخدم بشكل تفاعلي
        """
        print("\n" + "="*60)
        print("برنامج تحليل منحنيات الجريان في القنوات المفتوحة")
        print("="*60)
        
        # اختيار نوع القناة
        while True:
            print("\nاختر نوع القناة:")
            print("1. مستطيلة (Rectangular)")
            print("2. مثلثة (Triangular)")
            print("3. شبه منحرف (Trapezoidal)")
            
            try:
                choice = int(input("الرجاء إدخال رقم الاختيار (1-3): "))
                if choice in [1, 2, 3]:
                    break
                else:
                    print("❌ خطأ: الرجاء اختيار رقم بين 1 و 3")
            except ValueError:
                print("❌ خطأ: الرجاء إدخال رقم صحيح")
        
        # إدخال معاملات القناة
        print("\n" + "-"*40)
        print("معاملات القناة الهندسية:")
        print("-"*40)
        
        if choice == 1:  # مستطيلة
            self.channel_type = "rectangular"
            while True:
                try:
                    b = float(input("عرض القناة (متر): "))
                    if b > 0:
                        self.channel_params['b'] = b
                        self.channel_params['z'] = 0  # الميل الجانبي = 0
                        break
                    else:
                        print("❌ خطأ: يجب أن يكون العرض أكبر من صفر")
                except ValueError:
                    print("❌ خطأ: الرجاء إدخال رقم صحيح")
                    
        elif choice == 2:  # مثلثة
            self.channel_type = "triangular"
            while True:
                try:
                    z = float(input("الميل الجانبي (1:Z) أفقي:رأسي: "))
                    if z > 0:
                        self.channel_params['z'] = z
                        self.channel_params['b'] = 0
                        break
                    else:
                        print("❌ خطأ: يجب أن يكون الميل الجانبي أكبر من صفر")
                except ValueError:
                    print("❌ خطأ: الرجاء إدخال رقم صحيح")
                    
        else:  # شبه منحرف
            self.channel_type = "trapezoidal"
            while True:
                try:
                    b = float(input("عرض القاع (متر): "))
                    z = float(input("الميل الجانبي (1:Z) أفقي:رأسي: "))
                    if b > 0 and z > 0:
                        self.channel_params['b'] = b
                        self.channel_params['z'] = z
                        break
                    else:
                        print("❌ خطأ: يجب أن تكون القيم موجبة")
                except ValueError:
                    print("❌ خطأ: الرجاء إدخال أرقام صحيحة")
        
        # إدخال معاملات إضافية
        print("\n" + "-"*40)
        print("معاملات الجريان:")
        print("-"*40)
        
        while True:
            try:
                Q = float(input("معدل التصريف (م³/ث): "))
                if Q > 0:
                    self.flow_params['Q'] = Q
                    break
                else:
                    print("❌ خطأ: يجب أن يكون التصريف أكبر من صفر")
            except ValueError:
                print("❌ خطأ: الرجاء إدخال رقم صحيح")
        
        while True:
            try:
                S0 = float(input("ميل القناة (م/م): "))
                if S0 >= 0:
                    self.flow_params['S0'] = S0
                    break
                else:
                    print("❌ خطأ: يجب أن يكون الميل موجباً أو صفراً")
            except ValueError:
                print("❌ خطأ: الرجاء إدخال رقم صحيح")
        
        while True:
            try:
                n = float(input("معامل مانينغ للخشونة: "))
                if 0.008 <= n <= 0.15:
                    self.flow_params['n'] = n
                    break
                else:
                    print("❌ خطأ: معامل مانينغ يجب أن يكون بين 0.008 و 0.15")
            except ValueError:
                print("❌ خطأ: الرجاء إدخال رقم صحيح")
        
        while True:
            try:
                y_initial = float(input("العمق الابتدائي عند بداية القناة (متر): "))
                if y_initial > 0:
                    self.flow_params['y_initial'] = y_initial
                    break
                else:
                    print("❌ خطأ: يجب أن يكون العمق أكبر من صفر")
            except ValueError:
                print("❌ خطأ: الرجاء إدخال رقم صحيح")
        
        while True:
            try:
                L = float(input("طول القناة الكلي (متر): "))
                if L > 0:
                    self.flow_params['L'] = L
                    break
                else:
                    print("❌ خطأ: يجب أن يكون الطول أكبر من صفر")
            except ValueError:
                print("❌ خطأ: الرجاء إدخال رقم صحيح")
    
    def calculate_area(self, y):
        """حساب مساحة المقطع العرضي"""
        if self.channel_type == "rectangular":
            return self.channel_params['b'] * y
        elif self.channel_type == "triangular":
            return self.channel_params['z'] * y**2
        else:  # trapezoidal
            return (self.channel_params['b'] + self.channel_params['z'] * y) * y
    
    def calculate_wetted_perimeter(self, y):
        """حساب المحيط المبلل"""
        if self.channel_type == "rectangular":
            return self.channel_params['b'] + 2 * y
        elif self.channel_type == "triangular":
            return 2 * y * np.sqrt(1 + self.channel_params['z']**2)
        else:  # trapezoidal
            return self.channel_params['b'] + 2 * y * np.sqrt(1 + self.channel_params['z']**2)
    
    def calculate_hydraulic_radius(self, y):
        """حساب نصف القطر الهيدروليكي"""
        A = self.calculate_area(y)
        P = self.calculate_wetted_perimeter(y)
        return A / P if P > 0 else 0
    
    def calculate_top_width(self, y):
        """حساب عرض السطح العلوي"""
        if self.channel_type == "rectangular":
            return self.channel_params['b']
        elif self.channel_type == "triangular":
            return 2 * self.channel_params['z'] * y
        else:  # trapezoidal
            return self.channel_params['b'] + 2 * self.channel_params['z'] * y
    
    def critical_depth_equation(self, y):
        """معادلة العمق الحرجي"""
        A = self.calculate_area(y)
        T = self.calculate_top_width(y)
        if A <= 0 or T <= 0:
            return 1e10
        return self.flow_params['Q']**2 * T / (self.g * A**3) - 1
    
    def calculate_critical_depth(self):
        """حساب العمق الحرجي"""
        try:
            # البحث عن العمق الحرجي بين 0.01 و 100 متر
            yc = bisect(self.critical_depth_equation, 0.001, 100)
            return yc
        except:
            print("⚠️ تحذير: لم يتم العثور على العمق الحرجي، استخدام قيمة تقديرية")
            return 0.5
    
    def normal_depth_equation(self, y):
        """معادلة العمق المنتظم باستخدام صيغة مانينغ"""
        A = self.calculate_area(y)
        R = self.calculate_hydraulic_radius(y)
        if A <= 0 or R <= 0:
            return 1e10
        Q_calculated = (1/self.flow_params['n']) * A * R**(2/3) * np.sqrt(self.flow_params['S0'])
        return Q_calculated - self.flow_params['Q']
    
    def calculate_normal_depth(self):
        """حساب العمق المنتظم"""
        if self.flow_params['S0'] == 0:
            return float('inf')  # ميل أفقي، لا يوجد عمق منتظم
        
        try:
            yn = bisect(self.normal_depth_equation, 0.001, 100)
            return yn
        except:
            print("⚠️ تحذير: لم يتم العثور على العمق المنتظم")
            return None
    
    def calculate_froude_number(self, y):
        """حساب رقم فرود"""
        A = self.calculate_area(y)
        T = self.calculate_top_width(y)
        if A <= 0 or T <= 0:
            return 0
        V = self.flow_params['Q'] / A
        return V / np.sqrt(self.g * A / T)
    
    def classify_flow(self, y, yc, yn):
        """تصنيف نوع الجريان والمنحنى"""
        # تصنيف الجريان
        Fr = self.calculate_froude_number(y)
        if Fr < 1:
            regime = "دون الحرج (Subcritical)"
        elif Fr > 1:
            regime = "فوق الحرج (Supercritical)"
        else:
            regime = "حرج (Critical)"
        
        # تصنيف المنحنى
        if self.flow_params['S0'] == 0:
            curve_type = "قناة أفقية (Horizontal)"
        elif self.flow_params['S0'] < 0:
            curve_type = "قناة عكسية (Adverse)"
        elif yn is None or yn == float('inf'):
            curve_type = "غير محدد"
        else:
            # مقارنة العمق الفعلي مع العمق الحرجي والمنتظم
            if y > yn > yc:
                curve_type = "منحنى ناقص (M1) - Mild Slope"
            elif yn > y > yc:
                curve_type = "منحنى ناقص (M2) - Mild Slope"
            elif yn > yc > y:
                curve_type = "منحنى زائد (M3) - Mild Slope"
            elif y > yc > yn:
                curve_type = "منحنى ناقص (S1) - Steep Slope"
            elif yc > y > yn:
                curve_type = "منحنى زائد (S2) - Steep Slope"
            elif yc > yn > y:
                curve_type = "منحنى زائد (S3) - Steep Slope"
            elif y > yc and yn > yc:
                curve_type = "منحنى منتظم (C1) - Critical Slope"
            elif y < yc and yn < yc:
                curve_type = "منحنى منتظم (C3) - Critical Slope"
            else:
                curve_type = "غير محدد"
        
        return regime, curve_type
    
    def water_surface_profile_equation(self, x, y):
        """معادلة منحنى سطح الماء (معادلة التدرج الديناميكي)"""
        S0 = self.flow_params['S0']
        n = self.flow_params['n']
        Q = self.flow_params['Q']
        
        A = self.calculate_area(y)
        P = self.calculate_wetted_perimeter(y)
        T = self.calculate_top_width(y)
        
        if A <= 0 or T <= 0:
            return [0]
        
        # حساب رقم فرود
        Fr = self.calculate_froude_number(y)
        
        # حساب ميل خط الطاقة
        Sf = (n * Q / (A * (A/P)**(2/3)))**2
        
        # معادلة التدرج الديناميكي
        if abs(1 - Fr**2) < 1e-6:  # تجنب القسمة على صفر عند الجريان الحرج
            return [0]
        
        dydx = (S0 - Sf) / (1 - Fr**2)
        
        return [dydx]
    
    def calculate_water_surface_profile(self):
        """حساب منحنى سطح الماء على طول القناة"""
        y_initial = self.flow_params['y_initial']
        L = self.flow_params['L']
        
        # عدد النقاط للحساب
        x_points = np.linspace(0, L, 500)
        
        # حل المعادلة التفاضلية
        try:
            solution = solve_ivp(
                self.water_surface_profile_equation,
                [0, L],
                [y_initial],
                t_eval=x_points,
                method='RK45',
                rtol=1e-8,
                atol=1e-10
            )
            
            if solution.success:
                return solution.t, solution.y[0]
            else:
                print("⚠️ تحذير: فشل حل معادلة سطح الماء")
                return None, None
        except Exception as e:
            print(f"⚠️ خطأ في حساب منحنى سطح الماء: {e}")
            return None, None
    
    def plot_water_surface_profile(self, x, y, yc, yn):
        """رسم منحنى سطح الماء مع تحديد أنواع المنحنيات"""
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
        
        # الرسم العلوي: منحنى سطح الماء
        ax1.plot(x, y, 'b-', linewidth=2, label='سطح الماء')
        
        # خط العمق الحرجي
        if yc is not None:
            ax1.axhline(y=yc, color='r', linestyle='--', linewidth=1.5, 
                       label=f'العمق الحرجي (yc = {yc:.3f} م)')
        
        # خط العمق المنتظم
        if yn is not None and yn != float('inf'):
            ax1.axhline(y=yn, color='g', linestyle=':', linewidth=1.5, 
                       label=f'العمق المنتظم (yn = {yn:.3f} م)')
        
        # تلوين المناطق حسب نوع المنحنى
        if yc is not None and yn is not None and yn != float('inf'):
            # تحديد المناطق المختلفة
            for i in range(len(x) - 1):
                y_mid = (y[i] + y[i+1]) / 2
                regime, curve_type = self.classify_flow(y_mid, yc, yn)
                
                if "M1" in curve_type or "S1" in curve_type:
                    color = 'lightblue'
                    alpha = 0.3
                    label = 'منحنى ناقص (Backwater)'
                elif "M2" in curve_type:
                    color = 'lightgreen'
                    alpha = 0.3
                    label = 'منحنى ناقص (Drawdown)'
                elif "M3" in curve_type or "S3" in curve_type:
                    color = 'orange'
                    alpha = 0.3
                    label = 'منحنى زائد'
                elif "S2" in curve_type:
                    color = 'yellow'
                    alpha = 0.3
                    label = 'منحنى زائد'
                else:
                    color = 'gray'
                    alpha = 0.2
                    label = 'منحنى منتظم/غير محدد'
                
                ax1.fill_between(x[i:i+2], y[i:i+2], 0, 
                               color=color, alpha=alpha)
        
        # تنسيق الرسم العلوي
        ax1.set_xlabel('المسافة على طول القناة (م)', fontsize=12, fontweight='bold')
        ax1.set_ylabel('عمق المياه (م)', fontsize=12, fontweight='bold')
        ax1.set_title('منحنى سطح الماء في القناة المفتوحة', fontsize=14, fontweight='bold')
        ax1.grid(True, alpha=0.3)
        ax1.legend(loc='best')
        
        # الرسم السفلي: رقم فرود
        Fr = np.array([self.calculate_froude_number(yi) for yi in y])
        ax2.plot(x, Fr, 'r-', linewidth=2, label='رقم فرود')
        ax2.axhline(y=1, color='k', linestyle='--', linewidth=1, label='Fr = 1 (حرج)')
        
        # تلوين مناطق الجريان
        ax2.fill_between(x, Fr, 1, where=(Fr > 1), 
                        color='red', alpha=0.2, label='فوق الحرج')
        ax2.fill_between(x, Fr, 1, where=(Fr < 1), 
                        color='blue', alpha=0.2, label='دون الحرج')
        
        ax2.set_xlabel('المسافة على طول القناة (م)', fontsize=12, fontweight='bold')
        ax2.set_ylabel('رقم فرود', fontsize=12, fontweight='bold')
        ax2.set_title('تغير رقم فرود على طول القناة', fontsize=14, fontweight='bold')
        ax2.grid(True, alpha=0.3)
        ax2.legend(loc='best')
        
        plt.tight_layout()
        plt.show()
        
        # إنشاء منحنى تفصيلي إضافي
        self.plot_energy_grade_line(x, y)
    
    def plot_energy_grade_line(self, x, y):
        """رسم خط الطاقة ومنحنى سطح الماء"""
        fig, ax = plt.subplots(figsize=(12, 6))
        
        # حساب منسوب القاع
        z_bed = self.flow_params['L'] * self.flow_params['S0'] - x * self.flow_params['S0']
        
        # حساب سرعة الجريان وخط الطاقة
        V = np.array([self.flow_params['Q'] / self.calculate_area(yi) if self.calculate_area(yi) > 0 else 0 for yi in y])
        EGL = y + z_bed + V**2 / (2 * self.g)
        
        # رسم المنحنيات
        ax.plot(x, z_bed, 'brown', linewidth=2, label='قاع القناة')
        ax.plot(x, z_bed + y, 'b-', linewidth=2, label='سطح الماء')
        ax.plot(x, EGL, 'r--', linewidth=1.5, label='خط الطاقة الكلية')
        
        ax.fill_between(x, z_bed, z_bed + y, color='lightblue', alpha=0.3)
        ax.fill_between(x, z_bed, z_bed, color='brown', alpha=0.5)
        
        ax.set_xlabel('المسافة على طول القناة (م)', fontsize=12, fontweight='bold')
        ax.set_ylabel('المنسوب (م)', fontsize=12, fontweight='bold')
        ax.set_title('خط الطاقة ومنحنى سطح الماء', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='best')
        
        plt.tight_layout()
        plt.show()
    
    def display_results(self, x, y, yc, yn):
        """عرض النتائج التحليلية"""
        print("\n" + "="*60)
        print("النتائج التحليلية:")
        print("="*60)
        
        print(f"\nنوع القناة: {self.channel_type}")
        print(f"عرض القناة/القاع: {self.channel_params['b']:.3f} م")
        if self.channel_params['z'] > 0:
            print(f"الميل الجانبي: 1:{self.channel_params['z']:.2f}")
        
        print(f"\nمعاملات الجريان:")
        print(f"التصريف (Q): {self.flow_params['Q']:.3f} م³/ث")
        print(f"ميل القناة (S0): {self.flow_params['S0']:.6f}")
        print(f"معامل مانينغ (n): {self.flow_params['n']:.4f}")
        
        if yc:
            print(f"\nالعمق الحرجي (yc): {yc:.4f} م")
        if yn and yn != float('inf'):
            print(f"العمق المنتظم (yn): {yn:.4f} م")
        
        # معلومات عن المنحنى عند البداية والنهاية
        if x is not None and y is not None:
            y_start = y[0]
            y_end = y[-1]
            
            regime_start, curve_start = self.classify_flow(y_start, yc, yn)
            regime_end, curve_end = self.classify_flow(y_end, yc, yn)
            
            print(f"\nعند بداية القناة (x = 0 م):")
            print(f"  العمق: {y_start:.4f} م")
            print(f"  نوع الجريان: {regime_start}")
            print(f"  نوع المنحنى: {curve_start}")
            
            print(f"\nعند نهاية القناة (x = {x[-1]:.1f} م):")
            print(f"  العمق: {y_end:.4f} م")
            print(f"  نوع الجريان: {regime_end}")
            print(f"  نوع المنحنى: {curve_end}")
    
    def run_analysis(self):
        """تشغيل التحليل الكامل"""
        # الحصول على البيانات من المستخدم
        self.get_user_input()
        
        # الحسابات الأساسية
        print("\n" + "="*60)
        print("جاري إجراء الحسابات...")
        print("="*60)
        
        # حساب العمق الحرجي
        yc = self.calculate_critical_depth()
        print(f"✓ تم حساب العمق الحرجي: {yc:.4f} م")
        
        # حساب العمق المنتظم
        yn = self.calculate_normal_depth()
        if yn is not None and yn != float('inf'):
            print(f"✓ تم حساب العمق المنتظم: {yn:.4f} م")
        else:
            print("⚠️ لا يوجد عمق منتظم (ميل أفقي أو عكسي)")
        
        # حساب منحنى سطح الماء
        print("جاري حساب منحنى سطح الماء...")
        x, y = self.calculate_water_surface_profile()
        
        if x is not None and y is not None:
            print(f"✓ تم حساب منحنى سطح الماء بنجاح ({len(x)} نقطة)")
            
            # عرض النتائج
            self.display_results(x, y, yc, yn)
            
            # رسم المنحنيات
            print("\nجاري رسم المنحنيات...")
            self.plot_water_surface_profile(x, y, yc, yn)
            
        else:
            print("❌ فشل في حساب منحنى سطح الماء")
        
        return x, y, yc, yn


def main():
    """الدالة الرئيسية"""
    print("""
    ╔════════════════════════════════════════════════════════╗
    ║      برنامج تحليل منحنيات الجريان في القنوات المفتوحة      ║
    ║           Open Channel Flow Profile Analyzer           ║
    ╚════════════════════════════════════════════════════════╝
    """)
    
    print("📋 التعليمات:")
    print("• أدخل معاملات القناة والجريان بدقة")
    print("• تأكد من استخدام الوحدات المترية (SI)")
    print("• يمكن إدخال أرقام عشرية باستخدام النقطة (.)")
    print("• معامل مانينغ للخرسانة ≈ 0.013-0.015")
    print("• معامل مانينغ للتراب ≈ 0.020-0.030")
    
    # إنشاء محلل القناة
    channel = OpenChannelFlow()
    
    while True:
        # تشغيل التحليل
        channel.run_analysis()
        
        # سؤال المستخدم عن إجراء تحليل آخر
        print("\n" + "="*60)
        again = input("هل تريد إجراء تحليل آخر؟ (نعم/لا): ").strip().lower()
        if again not in ['نعم', 'yes', 'y', 'ن', '1']:
            print("\nشكراً لاستخدامك برنامج تحليل منحنيات الجريان!")
            print("تم التطوير بواسطة مهندس متخصص في الهيدروليكا")
            break
        else:
            # إعادة تعيين المعاملات
            channel = OpenChannelFlow()


# مثال على استخدام مباشر (اختياري)
def example_analysis():
    """مثال توضيحي مع بيانات افتراضية"""
    channel = OpenChannelFlow()
    
    # قناة مستطيلة
    channel.channel_type = "rectangular"
    channel.channel_params = {'b': 5.0, 'z': 0}
    
    # معاملات الجريان
    channel.flow_params = {
        'Q': 10.0,      # تصريف 10 م³/ث
        'S0': 0.001,    # ميل 0.001
        'n': 0.015,     # معامل مانينغ للخرسانة
        'y_initial': 2.0,  # عمق ابتدائي 2 م
        'L': 1000.0     # طول القناة 1000 م
    }
    
    print("\nتشغيل مثال توضيحي...")
    x, y, yc, yn = channel.run_analysis()
    return x, y, yc, yn


if __name__ == "__main__":
    # للتشغيل المباشر
    main()
    
    # أو لتشغيل المثال التوضيحي (علق السطر أعلاه وفك التعليق أدناه)
    # example_analysis()