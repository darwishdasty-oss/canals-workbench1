import numpy as np
import math
from dataclasses import dataclass
from typing import Tuple, Optional, Dict
from enum import Enum

class JumpType(Enum):
    """أنواع القفزة الهيدروليكية"""
    UNDULAR = "قفزة متموجة (Undular Jump) - Fr1: 1.0-1.7"
    WEAK = "قفزة ضعيفة (Weak Jump) - Fr1: 1.7-2.5"
    OSCILLATING = "قفزة متذبذبة (Oscillating Jump) - Fr1: 2.5-4.5"
    STEADY = "قفزة مستقرة (Steady Jump) - Fr1: 4.5-9.0"
    STRONG = "قفزة قوية (Strong Jump) - Fr1: > 9.0"

class BasinType(Enum):
    """أنواع أحواض التهدئة"""
    TYPE_I = "حوض تهدئة نوع I (USBR Type I) - للقفزات القوية"
    TYPE_II = "حوض تهدئة نوع II (USBR Type II) - للقفزات المتوسطة والقوية"
    TYPE_III = "حوض تهدئة نوع III (USBR Type III) - للقفزات الضعيفة والمتوسطة"
    TYPE_IV = "حوض تهدئة نوع IV (USBR Type IV) - للقفزات المتذبذبة والمستقرة"
    SLOPED = "حوض تهدئة مائل (Sloped Basin) - للقنوات ذات الانحدار"

@dataclass
class HydraulicJumpInput:
    """مدخلات القفزة الهيدروليكية"""
    velocity_u1: float  # سرعة التدفق قبل القفزة (م/ث)
    depth_y1: float     # عمق المياه قبل القفزة (م)
    width_b: float      # عرض المجرى (م)
    slope: float = 0.0  # ميل القناة (م/م)
    friction_coefficient: float = 0.015  # معامل الاحتكاك (ماننج)
    soil_type: str = "rock"  # نوع التربة

@dataclass
class HydraulicJumpResults:
    """نتائج تحليل القفزة الهيدروليكية"""
    froude_number_1: float
    froude_number_2: float
    depth_y2: float
    energy_loss: float
    energy_loss_percentage: float
    jump_efficiency: float
    jump_length: float
    jump_type: JumpType
    conjugate_depth_ratio: float

@dataclass
class StillingBasinDesign:
    """تصميم حوض التهدئة"""
    basin_type: BasinType
    basin_length: float
    basin_width: float
    basin_depth: float
    appurtenances_height: float
    end_sill_height: float
    baffle_blocks_height: float
    chute_blocks_height: float
    water_volume: float
    energy_dissipation_capacity: float

class HydraulicJumpCalculator:
    """حاسبة القفزة الهيدروليكية المتقدمة"""
    
    def __init__(self, g: float = 9.81):
        """
        تهيئة الحاسبة
        
        Parameters:
        -----------
        g : float
            تسارع الجاذبية (م/ث²)، القيمة الافتراضية 9.81
        """
        self.g = g
        
    def calculate_froude_number(self, velocity: float, depth: float) -> float:
        """
        حساب رقم فرويد
        
        Parameters:
        -----------
        velocity : float
            سرعة التدفق (م/ث)
        depth : float
            عمق المياه (م)
        
        Returns:
        --------
        float
            رقم فرويد
        """
        if depth <= 0:
            raise ValueError("عمق المياه يجب أن يكون أكبر من صفر")
        return velocity / math.sqrt(self.g * depth)
    
    def determine_jump_type(self, fr1: float) -> JumpType:
        """
        تحديد نوع القفزة الهيدروليكية بناءً على رقم فرويد
        
        Parameters:
        -----------
        fr1 : float
            رقم فرويد قبل القفزة
        
        Returns:
        --------
        JumpType
            نوع القفزة الهيدروليكية
        """
        if fr1 < 1.0:
            raise ValueError("لا توجد قفزة هيدروليكية (Fr1 < 1.0)")
        elif 1.0 <= fr1 < 1.7:
            return JumpType.UNDULAR
        elif 1.7 <= fr1 < 2.5:
            return JumpType.WEAK
        elif 2.5 <= fr1 < 4.5:
            return JumpType.OSCILLATING
        elif 4.5 <= fr1 < 9.0:
            return JumpType.STEADY
        else:
            return JumpType.STRONG
    
    def calculate_conjugate_depth(self, y1: float, fr1: float) -> float:
        """
        حساب العمق المرافق (y2) باستخدام معادلة بيلانجيه
        
        Parameters:
        -----------
        y1 : float
            العمق قبل القفزة (م)
        fr1 : float
            رقم فرويد قبل القفزة
        
        Returns:
        --------
        float
            العمق بعد القفزة (م)
        """
        y2 = (y1 / 2) * (math.sqrt(1 + 8 * fr1**2) - 1)
        return y2
    
    def calculate_energy_loss(self, y1: float, y2: float, fr1: float) -> Tuple[float, float]:
        """
        حساب الطاقة المفقودة في القفزة الهيدروليكية
        
        Parameters:
        -----------
        y1 : float
            العمق قبل القفزة (م)
        y2 : float
            العمق بعد القفزة (م)
        fr1 : float
            رقم فرويد قبل القفزة
        
        Returns:
        --------
        Tuple[float, float]
            الطاقة المفقودة (م) ونسبة الفقد المئوية
        """
        # الطاقة المفقودة باستخدام معادلة الفقد في القفزة
        delta_E = (y2 - y1)**3 / (4 * y1 * y2)
        
        # الطاقة الكلية قبل القفزة
        E1 = y1 + (self.g * y1 * fr1**2) / (2 * self.g)
        
        # نسبة الفقد المئوية
        energy_loss_percentage = (delta_E / E1) * 100 if E1 > 0 else 0
        
        return delta_E, energy_loss_percentage
    
    def calculate_jump_length(self, y2: float, fr1: float) -> float:
        """
        حساب طول القفزة الهيدروليكية
        
        Parameters:
        -----------
        y2 : float
            العمق بعد القفزة (م)
        fr1 : float
            رقم فرويد قبل القفزة
        
        Returns:
        --------
        float
            طول القفزة (م)
        """
        # معادلات تجريبية مختلفة لحساب طول القفزة
        if fr1 < 5:
            # معادلة Silvester للقفزات الضعيفة
            Lj = 9.75 * y2 * (fr1 - 1)**0.01
        else:
            # معادلة USBR للقفزات القوية
            Lj = 6.1 * y2
        
        return Lj
    
    def analyze_jump(self, input_data: HydraulicJumpInput) -> HydraulicJumpResults:
        """
        تحليل كامل للقفزة الهيدروليكية
        
        Parameters:
        -----------
        input_data : HydraulicJumpInput
            بيانات المدخلات
        
        Returns:
        --------
        HydraulicJumpResults
            نتائج التحليل الكامل
        """
        # حساب رقم فرويد قبل القفزة
        fr1 = self.calculate_froude_number(input_data.velocity_u1, input_data.depth_y1)
        
        # حساب العمق المرافق
        y2 = self.calculate_conjugate_depth(input_data.depth_y1, fr1)
        
        # حساب الطاقة المفقودة
        delta_E, energy_loss_percentage = self.calculate_energy_loss(
            input_data.depth_y1, y2, fr1
        )
        
        # حساب طول القفزة
        Lj = self.calculate_jump_length(y2, fr1)
        
        # تحديد نوع القفزة
        jump_type = self.determine_jump_type(fr1)
        
        # حساب رقم فرويد بعد القفزة
        fr2 = self.calculate_froude_number(
            input_data.velocity_u1 * input_data.depth_y1 / y2, y2
        )
        
        # حساب كفاءة القفزة
        efficiency = (1 - delta_E / (input_data.depth_y1 + 
                    input_data.velocity_u1**2/(2*self.g))) * 100
        
        # نسبة العمق المرافق
        conjugate_depth_ratio = y2 / input_data.depth_y1
        
        return HydraulicJumpResults(
            froude_number_1=fr1,
            froude_number_2=fr2,
            depth_y2=y2,
            energy_loss=delta_E,
            energy_loss_percentage=energy_loss_percentage,
            jump_efficiency=efficiency,
            jump_length=Lj,
            jump_type=jump_type,
            conjugate_depth_ratio=conjugate_depth_ratio
        )

class StillingBasinDesigner:
    """مصمم أحواض التهدئة"""
    
    def __init__(self, g: float = 9.81):
        """
        تهيئة المصمم
        
        Parameters:
        -----------
        g : float
            تسارع الجاذبية (م/ث²)
        """
        self.g = g
    
    def select_basin_type(self, jump_results: HydraulicJumpResults, 
                         slope: float) -> BasinType:
        """
        اختيار نوع حوض التهدئة المناسب
        
        Parameters:
        -----------
        jump_results : HydraulicJumpResults
            نتائج تحليل القفزة
        slope : float
            ميل القناة
        
        Returns:
        --------
        BasinType
            نوع الحوض المناسب
        """
        fr1 = jump_results.froude_number_1
        
        if slope > 0.05:  # ميل كبير
            return BasinType.SLOPED
        elif fr1 > 9.0:
            return BasinType.TYPE_I
        elif 4.5 <= fr1 <= 9.0:
            if jump_results.conjugate_depth_ratio > 5:
                return BasinType.TYPE_II
            else:
                return BasinType.TYPE_IV
        elif 2.5 <= fr1 < 4.5:
            return BasinType.TYPE_III
        else:
            return BasinType.TYPE_IV
    
    def design_basin(self, input_data: HydraulicJumpInput, 
                    jump_results: HydraulicJumpResults,
                    safety_factor: float = 1.15) -> StillingBasinDesign:
        """
        تصميم حوض التهدئة
        
        Parameters:
        -----------
        input_data : HydraulicJumpInput
            بيانات المدخلات
        jump_results : HydraulicJumpResults
            نتائج تحليل القفزة
        safety_factor : float
            معامل الأمان (1.0 - 1.25)
        
        Returns:
        --------
        StillingBasinDesign
            تصميم الحوض
        """
        basin_type = self.select_basin_type(jump_results, input_data.slope)
        
        # أبعاد أساسية
        basin_width = input_data.width_b * 1.1  # توسيع بسيط للعرض
        
        # حساب طول الحوض بناءً على نوعه
        if basin_type == BasinType.TYPE_I:
            basin_length = 6.0 * jump_results.depth_y2
        elif basin_type == BasinType.TYPE_II:
            basin_length = 4.0 * jump_results.depth_y2
        elif basin_type == BasinType.TYPE_III:
            basin_length = 2.8 * jump_results.depth_y2
        elif basin_type == BasinType.TYPE_IV:
            basin_length = 5.0 * jump_results.depth_y2
        else:  # SLOPED
            basin_length = jump_results.jump_length * 1.3
        
        basin_length *= safety_factor
        
        # عمق الحوض
        basin_depth = jump_results.depth_y2 * 1.2
        
        # ارتفاع الملحقات
        if jump_results.froude_number_1 > 4.5:
            appurtenances_height = jump_results.depth_y2 * 0.8
            end_sill_height = jump_results.depth_y2 * 0.4
            baffle_blocks_height = jump_results.depth_y2 * 0.8
            chute_blocks_height = input_data.depth_y1 * 2.0  # FIX v1.3: was jump_results.depth_y1
        else:
            appurtenances_height = jump_results.depth_y2 * 0.5
            end_sill_height = jump_results.depth_y2 * 0.3
            baffle_blocks_height = jump_results.depth_y2 * 0.5
            chute_blocks_height = input_data.depth_y1 * 1.5  # FIX v1.3: was jump_results.depth_y1
        
        # حساب حجم المياه
        water_volume = basin_length * basin_width * jump_results.depth_y2
        
        # حساب قدرة تبديد الطاقة
        energy_dissipation_capacity = (
            self.g * water_volume * jump_results.energy_loss / 
            (jump_results.jump_length * input_data.width_b)
        )
        
        return StillingBasinDesign(
            basin_type=basin_type,
            basin_length=basin_length,
            basin_width=basin_width,
            basin_depth=basin_depth,
            appurtenances_height=appurtenances_height,
            end_sill_height=end_sill_height,
            baffle_blocks_height=baffle_blocks_height,
            chute_blocks_height=chute_blocks_height,
            water_volume=water_volume,
            energy_dissipation_capacity=energy_dissipation_capacity
        )

class HydraulicJumpAnalyzer:
    """المحلل الرئيسي للنظام"""
    
    def __init__(self):
        self.calculator = HydraulicJumpCalculator()
        self.designer = StillingBasinDesigner()
    
    def validate_inputs(self, input_data: HydraulicJumpInput) -> bool:
        """
        التحقق من صحة المدخلات
        
        Parameters:
        -----------
        input_data : HydraulicJumpInput
            بيانات المدخلات
        
        Returns:
        --------
        bool
            صحة المدخلات
        """
        errors = []
        
        if input_data.depth_y1 <= 0:
            errors.append("عمق المياه يجب أن يكون أكبر من صفر")
        
        if input_data.velocity_u1 <= 0:
            errors.append("سرعة التدفق يجب أن تكون أكبر من صفر")
        
        if input_data.width_b <= 0:
            errors.append("عرض المجرى يجب أن يكون أكبر من صفر")
        
        if input_data.slope < 0:
            errors.append("الميل لا يمكن أن يكون سالباً")
        
        if errors:
            print("⚠️ أخطاء في المدخلات:")
            for error in errors:
                print(f"  - {error}")
            return False
        
        # التحقق من رقم فرويد
        fr1 = input_data.velocity_u1 / math.sqrt(9.81 * input_data.depth_y1)
        if fr1 < 1.0:
            print("⚠️ تحذير: رقم فرويد أقل من 1.0 - لن تتكون قفزة هيدروليكية")
            return False
        
        return True
    
    def analyze_and_design(self, input_data: HydraulicJumpInput) -> Tuple[HydraulicJumpResults, StillingBasinDesign]:
        """
        تحليل القفزة الهيدروليكية وتصميم حوض التهدئة
        
        Parameters:
        -----------
        input_data : HydraulicJumpInput
            بيانات المدخلات
        
        Returns:
        --------
        Tuple[HydraulicJumpResults, StillingBasinDesign]
            نتائج التحليل وتصميم الحوض
        """
        if not self.validate_inputs(input_data):
            raise ValueError("المدخلات غير صالحة")
        
        # تحليل القفزة
        jump_results = self.calculator.analyze_jump(input_data)
        
        # تصميم الحوض
        basin_design = self.designer.design_basin(input_data, jump_results)
        
        return jump_results, basin_design
    
    def print_results(self, input_data: HydraulicJumpInput,
                     jump_results: HydraulicJumpResults,
                     basin_design: StillingBasinDesign):
        """
        طباعة النتائج بشكل منسق
        
        Parameters:
        -----------
        input_data : HydraulicJumpInput
            بيانات المدخلات
        jump_results : HydraulicJumpResults
            نتائج تحليل القفزة
        basin_design : StillingBasinDesign
            تصميم الحوض
        """
        print("\n" + "="*70)
        print("                 نتائج تحليل وتصميم القفزة الهيدروليكية")
        print("="*70)
        
        print("\n📊 البيانات المدخلة:")
        print("-"*40)
        print(f"  • سرعة التدفق (u1): {input_data.velocity_u1:.3f} م/ث")
        print(f"  • عمق المياه (y1): {input_data.depth_y1:.3f} م")
        print(f"  • عرض المجرى (b): {input_data.width_b:.3f} م")
        print(f"  • ميل القناة: {input_data.slope:.4f} م/م")
        print(f"  • معامل الاحتكاك (n): {input_data.friction_coefficient:.4f}")
        
        print("\n📈 نتائج تحليل القفزة الهيدروليكية:")
        print("-"*40)
        print(f"  • رقم فرويد قبل القفزة (Fr1): {jump_results.froude_number_1:.3f}")
        print(f"  • رقم فرويد بعد القفزة (Fr2): {jump_results.froude_number_2:.3f}")
        print(f"  • عمق المياه بعد القفزة (y2): {jump_results.depth_y2:.3f} م")
        print(f"  • نسبة العمق المرافق (y2/y1): {jump_results.conjugate_depth_ratio:.3f}")
        print(f"  • الطاقة المفقودة: {jump_results.energy_loss:.3f} م")
        print(f"  • نسبة فقد الطاقة: {jump_results.energy_loss_percentage:.2f}%")
        print(f"  • كفاءة القفزة: {jump_results.jump_efficiency:.2f}%")
        print(f"  • طول القفزة: {jump_results.jump_length:.3f} م")
        
        print(f"\n🎯 نوع القفزة الهيدروليكية:")
        print(f"  {jump_results.jump_type.value}")
        
        print(f"\n🏗️ تصميم حوض التهدئة:")
        print("-"*40)
        print(f"  • نوع الحوض: {basin_design.basin_type.value}")
        print(f"  • طول الحوض: {basin_design.basin_length:.3f} م")
        print(f"  • عرض الحوض: {basin_design.basin_width:.3f} م")
        print(f"  • عمق الحوض: {basin_design.basin_depth:.3f} م")
        print(f"  • ارتفاع الملحقات: {basin_design.appurtenances_height:.3f} م")
        print(f"  • ارتفاع العتبة النهائية: {basin_design.end_sill_height:.3f} م")
        print(f"  • ارتفاع كتل التشتيت: {basin_design.baffle_blocks_height:.3f} م")
        print(f"  • ارتفاع كتل المدخل: {basin_design.chute_blocks_height:.3f} م")
        print(f"  • حجم المياه في الحوض: {basin_design.water_volume:.2f} م³")
        print(f"  • قدرة تبديد الطاقة: {basin_design.energy_dissipation_capacity:.2f} واط/م²")
        
        print(f"\n📋 توصيات التصميم:")
        print("-"*40)
        self._print_recommendations(jump_results, basin_design)
        
        print("\n" + "="*70)
    
    def _print_recommendations(self, jump_results: HydraulicJumpResults, 
                              basin_design: StillingBasinDesign):
        """طباعة توصيات التصميم"""
        recommendations = []
        
        if jump_results.froude_number_1 > 9.0:
            recommendations.append("• يوصى بتعزيز قاع الحوض بمواد مقاومة للتآكل")
            recommendations.append("• يجب توفير تهوية مناسبة لتجنب التكهف")
        
        if jump_results.energy_loss_percentage > 70:
            recommendations.append("• كفاءة تبديد طاقة ممتازة - التصميم فعال")
        elif jump_results.energy_loss_percentage < 40:
            recommendations.append("• كفاءة تبديد طاقة منخفضة - قد تحتاج لتحسين التصميم")
        
        if basin_design.basin_length / jump_results.depth_y2 < 4:
            recommendations.append("• تحذير: طول الحوض قصير نسبياً - قد لا يحتوي القفزة بالكامل")
        
        if jump_results.conjugate_depth_ratio > 10:
            recommendations.append("• يوصى بحوض تهدئة متدرج لتقليل الاضطرابات")
        
        recommendations.append("• يجب عمل صيانة دورية لملحقات الحوض")
        recommendations.append("• مراقبة التآكل في منطقة تأثير القفزة")
        
        for rec in recommendations:
            print(rec)

# واجهة المستخدم التفاعلية
def interactive_menu():
    """القائمة التفاعلية للبرنامج"""
    print("\n" + "="*70)
    print("     برنامج تحليل وتصميم القفزة الهيدروليكية وأحواض التهدئة")
    print("               إصدار 1.0 - مهندس مائي متخصص")
    print("="*70)
    
    analyzer = HydraulicJumpAnalyzer()
    
    while True:
        print("\n📋 القائمة الرئيسية:")
        print("-"*40)
        print("1. إدخال بيانات جديدة وتحليل")
        print("2. عرض مثال توضيحي")
        print("3. معايير التصميم والإرشادات")
        print("4. خروج")
        
        choice = input("\nاختر رقم العملية (1-4): ").strip()
        
        if choice == '1':
            try:
                # إدخال البيانات
                print("\n📝 إدخال البيانات:")
                print("-"*40)
                u1 = float(input("سرعة التدفق قبل القفزة (م/ث): "))
                y1 = float(input("عمق المياه قبل القفزة (م): "))
                b = float(input("عرض المجرى (م): "))
                slope = float(input("ميل القناة (م/م) [0 للمستوي]: ") or "0")
                n = float(input("معامل ماننج للاحتكاك [0.015]: ") or "0.015")
                
                # إنشاء كائن المدخلات
                input_data = HydraulicJumpInput(
                    velocity_u1=u1,
                    depth_y1=y1,
                    width_b=b,
                    slope=slope,
                    friction_coefficient=n
                )
                
                # التحليل والتصميم
                jump_results, basin_design = analyzer.analyze_and_design(input_data)
                
                # عرض النتائج
                analyzer.print_results(input_data, jump_results, basin_design)
                
            except ValueError as e:
                print(f"\n❌ خطأ: {e}")
            except Exception as e:
                print(f"\n❌ خطأ غير متوقع: {e}")
        
        elif choice == '2':
            # مثال توضيحي
            print("\n📚 مثال توضيحي:")
            print("-"*40)
            example_data = HydraulicJumpInput(
                velocity_u1=8.0,
                depth_y1=0.5,
                width_b=5.0,
                slope=0.02,
                friction_coefficient=0.015
            )
            
            print("بيانات المثال:")
            print(f"  • سرعة التدفق: {example_data.velocity_u1} م/ث")
            print(f"  • عمق المياه: {example_data.depth_y1} م")
            print(f"  • عرض المجرى: {example_data.width_b} م")
            
            jump_results, basin_design = analyzer.analyze_and_design(example_data)
            analyzer.print_results(example_data, jump_results, basin_design)
            
            input("\nاضغط Enter للمتابعة...")
        
        elif choice == '3':
            # معايير التصميم
            print_design_standards()
            input("\nاضغط Enter للمتابعة...")
        
        elif choice == '4':
            print("\nشكراً لاستخدام البرنامج. مع تمنياتنا بتصميم آمن وفعال!")
            break
        
        else:
            print("❌ اختيار غير صالح. الرجاء اختيار رقم من 1 إلى 4")

def print_design_standards():
    """طباعة معايير التصميم والإرشادات"""
    print("\n📚 معايير التصميم والإرشادات:")
    print("-"*60)
    print("""
    أنواع أحواض التهدئة (USBR):
    
    1. حوض نوع I (Type I):
       - للقفزات القوية (Fr1 > 9.0)
       - الطول: 6 × y2
       - يستخدم في السدود العالية والمفيضات الكبيرة
    
    2. حوض نوع II (Type II):
       - للقفزات المتوسطة إلى القوية (4.5 < Fr1 < 9.0)
       - الطول: 4 × y2
       - يحتوي على كتل تشتيت وعتبة نهائية
    
    3. حوض نوع III (Type III):
       - للقفزات الضعيفة إلى المتوسطة (2.5 < Fr1 < 4.5)
       - الطول: 2.8 × y2
       - مناسب للقنوات الصغيرة والمتوسطة
    
    4. حوض نوع IV (Type IV):
       - للقفزات المتذبذبة والمستقرة (2.5 < Fr1 < 4.5)
       - الطول: 5 × y2
       - تصميم خاص للتحكم في التموجات
    
    نصائح تصميمية:
    • استخدم معامل أمان 1.15-1.25 في الأبعاد
    • تأكد من ارتفاع العتبة النهائية المناسب
    • وفر تهوية كافية لمنطقة القفزة
    • استخدم خرسانة عالية المقاومة للتآكل
    """)

# نقطة التشغيل الرئيسية
if __name__ == "__main__":
    try:
        # عرض معلومات البرنامج
        print("="*70)
        print("     ⚙️  نظام تحليل وتصميم القفزة الهيدروليكية وأحواض التهدئة")
        print("         Hydraulic Jump Analysis & Stilling Basin Design")
        print("="*70)
        
        # تشغيل القائمة التفاعلية
        interactive_menu()
        
    except KeyboardInterrupt:
        print("\n\nتم إنهاء البرنامج بواسطة المستخدم.")
    except Exception as e:
        print(f"\n❌ خطأ في النظام: {e}")