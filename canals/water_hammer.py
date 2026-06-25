#!/usr/bin/env python3
"""
Water Hammer Analysis Tool - أداة تحليل ظاهرة المطرقة المائية
=============================================================
Professional engineering tool for calculating water hammer pressure
in pipeline systems and providing mitigation recommendations.

Author: Senior Hydraulic Software Engineer
Version: 2.0
License: Engineering Use Only
"""

import math
import sys
from typing import Dict, Tuple, List, Optional
import json
from dataclasses import dataclass
from enum import Enum

class PipeMaterial(Enum):
    """مواد الأنابيب الشائعة مع خواصها الميكانيكية"""
    STEEL = ("Steel", 200e9, 0.3, 400e6)  # (Name, E_modulus, Poisson, Yield_Strength)
    CAST_IRON = ("Cast Iron", 100e9, 0.26, 200e6)
    PVC = ("PVC", 3.0e9, 0.38, 50e6)
    HDPE = ("HDPE", 1.0e9, 0.45, 25e6)
    CONCRETE = ("Concrete", 30e9, 0.2, 40e6)
    COPPER = ("Copper", 110e9, 0.34, 210e6)

@dataclass
class PipeParameters:
    """معاملات الأنبوب"""
    length: float  # m
    diameter: float  # m
    wall_thickness: float  # m
    elastic_modulus: float  # Pa
    poisson_ratio: float = 0.3
    yield_strength: float = 400e6  # Pa
    
    @property
    def cross_section_area(self) -> float:
        """مساحة مقطع الأنبوب"""
        return math.pi * (self.diameter / 2) ** 2
    
    @property
    def diameter_to_thickness_ratio(self) -> float:
        """نسبة القطر إلى السمك"""
        return self.diameter / self.wall_thickness

@dataclass
class FluidProperties:
    """خواص المائع"""
    density: float  # kg/m³
    bulk_modulus: float = 2.2e9  # Pa (Bulk modulus of water)
    temperature: float = 20.0  # Celsius
    
    @property
    def sonic_velocity_unconfined(self) -> float:
        """سرعة الصوت في المائع غير المحصور"""
        return math.sqrt(self.bulk_modulus / self.density)

class WaterHammerAnalyzer:
    """
    محلل ظاهرة المطرقة المائية
    يقوم بحساب ضغط المطرقة المائية وتقديم توصيات هندسية
    """
    
    def __init__(self):
        self.results = {}
        
    def calculate_wave_speed(self, pipe: PipeParameters, fluid: FluidProperties) -> float:
        """
        حساب سرعة الموجة في الأنبوب باستخدام معادلة Korteweg
        
        a = sqrt(K/ρ / (1 + (K/E)*(D/e)*C))
        حيث:
        K: معامل المرونة الحجمي للمائع
        E: معامل يونغ لمادة الأنبوب
        D: قطر الأنبوب
        e: سمك الجدار
        C: ثابت يعتمد على ظروف التثبيت
        """
        # عامل التثبيت (للأنابيب المثبتة من طرف واحد)
        C1 = 1.0 - pipe.poisson_ratio**2  # مثبت من طرف واحد مع وصلات تمدد
        C2 = 1.0 - pipe.poisson_ratio**2  # مثبت من الطرفين (الأكثر شيوعاً)
        C3 = 1.0  # مدفون بالكامل
        
        # استخدام الحالة الأكثر تحفظاً (الأنبوب المثبت من الطرفين)
        support_factor = C2
        
        # حساب سرعة الموجة
        K_over_E = fluid.bulk_modulus / pipe.elastic_modulus
        D_over_e = pipe.diameter / pipe.wall_thickness
        
        denominator = 1.0 + K_over_E * D_over_e * support_factor
        
        if denominator <= 0:
            raise ValueError("خطأ في حساب سرعة الموجة: المقام غير صحيح")
        
        wave_speed = math.sqrt(fluid.bulk_modulus / (fluid.density * denominator))
        
        return wave_speed
    
    def calculate_joukowsky_pressure(self, wave_speed: float, velocity_change: float, 
                                    fluid_density: float) -> float:
        """
        حساب ضغط المطرقة المائية باستخدام معادلة Joukowsky
        
        ΔP = ρ * a * ΔV
        حيث:
        ρ: كثافة المائع
        a: سرعة الموجة
        ΔV: التغير في السرعة
        """
        pressure_change = fluid_density * wave_speed * abs(velocity_change)
        return pressure_change
    
    def calculate_critical_time(self, pipe_length: float, wave_speed: float) -> float:
        """
        حساب الزمن الحرج لإغلاق الصمام
        إذا كان زمن الإغلاق أقل من الزمن الحرج، تحدث مطرقة مائية كاملة
        """
        return 2.0 * pipe_length / wave_speed
    
    def calculate_pressure_rise_time(self, pipe_length: float, wave_speed: float) -> float:
        """
        حساب زمن ارتفاع الضغط (وقت وصول الموجة الأولى)
        """
        return pipe_length / wave_speed
    
    def analyze_valve_closure(self, pipe: PipeParameters, fluid: FluidProperties,
                             flow_velocity: float, closure_time: float) -> Dict:
        """
        تحليل إغلاق الصمام وحساب الضغط الناتج
        """
        # حساب سرعة الموجة
        wave_speed = self.calculate_wave_speed(pipe, fluid)
        
        # حساب الزمن الحرج
        critical_time = self.calculate_critical_time(pipe.length, wave_speed)
        
        # تحديد نوع الإغلاق (سريع أم بطيء)
        if closure_time <= critical_time:
            # إغلاق سريع - مطرقة مائية كاملة
            velocity_change = flow_velocity
            closure_type = "إغلاق سريع (مطرقة مائية كاملة)"
        else:
            # إغلاق بطيء - مطرقة مائية جزئية
            velocity_change = flow_velocity * (critical_time / closure_time)
            closure_type = "إغلاق بطيء (مطرقة مائية جزئية)"
        
        # حساب ضغط Joukowsky
        delta_pressure = self.calculate_joukowsky_pressure(
            wave_speed, velocity_change, fluid.density
        )
        
        # تحويل الضغط إلى وحدات مختلفة
        delta_pressure_bar = delta_pressure / 1e5
        delta_pressure_psi = delta_pressure / 6894.76
        
        # حساب الإجهاد في جدار الأنبوب
        hoop_stress = (delta_pressure * pipe.diameter) / (2 * pipe.wall_thickness)
        
        # حساب عامل الأمان
        safety_factor = pipe.yield_strength / hoop_stress if hoop_stress > 0 else float('inf')
        
        return {
            'wave_speed': wave_speed,
            'critical_time': critical_time,
            'closure_type': closure_type,
            'velocity_change': velocity_change,
            'delta_pressure_pa': delta_pressure,
            'delta_pressure_bar': delta_pressure_bar,
            'delta_pressure_psi': delta_pressure_psi,
            'hoop_stress': hoop_stress,
            'safety_factor': safety_factor,
            'pressure_rise_time': self.calculate_pressure_rise_time(pipe.length, wave_speed)
        }
    
    def get_mitigation_recommendations(self, analysis_results: Dict, 
                                      operating_pressure_bar: float) -> List[str]:
        """
        تقديم توصيات للحد من تأثير المطرقة المائية
        """
        recommendations = []
        
        delta_p_bar = analysis_results['delta_pressure_bar']
        max_pressure = operating_pressure_bar + delta_p_bar
        safety_factor = analysis_results['safety_factor']
        
        # تحليل المخاطر
        if safety_factor < 1.5:
            recommendations.append(
                "⚠️ تحذير عاجل: عامل الأمان منخفض جداً (< 1.5). "
                "احتمال كبير لحدوث فشل في الأنبوب!"
            )
        
        if delta_p_bar > 20:
            recommendations.append(
                "🔴 ضغط المطرقة المائية مرتفع جداً (> 20 bar). "
                "يجب اتخاذ إجراءات فورية."
            )
        
        # توصيات تخفيف الضغط
        if analysis_results['critical_time'] < 1.0:
            recommendations.append(
                "• زيادة زمن إغلاق الصمام إلى {} ثانية على الأقل لتجنب الإغلاق السريع".format(
                    math.ceil(analysis_results['critical_time'] * 1.5)
                )
            )
        
        if analysis_results['safety_factor'] < 2.0:
            recommendations.append(
                "• تركيب صمامات تخفيف الضغط (Pressure Relief Valves) عند النقاط الحرجة"
            )
            recommendations.append(
                "• إضافة خزانات تمدد هوائية (Air Chambers) لامتصاص الصدمات"
            )
        
        if analysis_results['hoop_stress'] > 100e6:
            recommendations.append(
                "• استخدام أنابيب ذات سمك جدار أكبر لتقليل الإجهاد"
            )
            recommendations.append(
                "• النظر في استخدام مواد أنابيب ذات مرونة أعلى (مثل HDPE)"
            )
        
        recommendations.append(
            "• تركيب صمامات عدم رجوع مخمدة (Damped Check Valves)"
        )
        recommendations.append(
            "• استخدام أنظمة التحكم التدريجي في المضخات (Soft Starters)"
        )
        recommendations.append(
            "• عمل صيانة دورية لصمامات الهواء والتفريغ"
        )
        
        if max_pressure > 40:
            recommendations.append(
                "🔴 تنبيه: الضغط الكلي يتجاوز 40 بار. "
                "يجب إعادة تصميم النظام بالكامل!"
            )
        
        return recommendations

class UserInterface:
    """واجهة المستخدم التفاعلية"""
    
    @staticmethod
    def print_header():
        """طباعة رأس البرنامج"""
        print("\n" + "="*80)
        print("     🌊 WATER HAMMER ANALYSIS TOOL - أداة تحليل المطرقة المائية 🌊")
        print("="*80)
        print("Professional Pipeline Hydraulic Analysis System")
        print("Version 2.0 | Engineering Grade Calculations\n")
    
    @staticmethod
    def get_float_input(prompt: str, min_val: float = 0, max_val: float = float('inf'),
                       unit: str = "", default: Optional[float] = None) -> float:
        """الحصول على إدخال رقمي من المستخدم مع التحقق من صحته"""
        while True:
            try:
                if default is not None:
                    user_input = input(f"{prompt} [{default} {unit}]: ").strip()
                    if user_input == "":
                        return default
                else:
                    user_input = input(f"{prompt} ({unit}): ").strip()
                
                value = float(user_input)
                
                if value < min_val or value > max_val:
                    print(f"❌ القيمة يجب أن تكون بين {min_val} و {max_val}")
                    continue
                
                return value
            except ValueError:
                print("❌ الرجاء إدخال قيمة رقمية صحيحة")
            except KeyboardInterrupt:
                print("\n\nتم إلغاء العملية من قبل المستخدم")
                sys.exit(0)
    
    @staticmethod
    def select_pipe_material() -> PipeMaterial:
        """اختيار مادة الأنبوب من القائمة"""
        print("\n" + "-"*60)
        print("اختر مادة الأنبوب:")
        materials = list(PipeMaterial)
        for i, material in enumerate(materials, 1):
            name, E, _, yield_strength = material.value
            print(f"  {i}. {name} (E={E/1e9:.1f} GPa, σy={yield_strength/1e6:.0f} MPa)")
        
        while True:
            try:
                choice = int(input(f"\nاختر رقم المادة (1-{len(materials)}): "))
                if 1 <= choice <= len(materials):
                    return materials[choice - 1]
                else:
                    print(f"❌ الرجاء اختيار رقم بين 1 و {len(materials)}")
            except ValueError:
                print("❌ الرجاء إدخال رقم صحيح")
            except KeyboardInterrupt:
                print("\n\nتم إلغاء العملية")
                sys.exit(0)
    
    @staticmethod
    def display_results(analysis: Dict, pipe: PipeParameters, fluid: FluidProperties,
                       operating_pressure_bar: float, recommendations: List[str]):
        """عرض النتائج بشكل مفصل ومنظم"""
        print("\n" + "="*80)
        print("                    📊 نتائج التحليل الهندسي")
        print("="*80)
        
        # معلمات الحساب
        print("\n📐 معلمات الحساب الأساسية:")
        print(f"   • سرعة الموجة في الأنبوب: {analysis['wave_speed']:.2f} m/s")
        print(f"   • الزمن الحرج لإغلاق الصمام: {analysis['critical_time']:.3f} ثانية")
        print(f"   • زمن ارتفاع الضغط: {analysis['pressure_rise_time']:.3f} ثانية")
        print(f"   • التغير في سرعة التدفق: {analysis['velocity_change']:.3f} m/s")
        
        # نتائج الضغط
        print("\n💥 نتائج ضغط المطرقة المائية:")
        print(f"   • نوع الإغلاق: {analysis['closure_type']}")
        print(f"   • الضغط الإضافي الناتج: {analysis['delta_pressure_bar']:.2f} bar")
        print(f"   • الضغط الإضافي: {analysis['delta_pressure_pa']/1000:.2f} kPa")
        print(f"   • الضغط الإضافي: {analysis['delta_pressure_psi']:.2f} psi")
        
        total_pressure = operating_pressure_bar + analysis['delta_pressure_bar']
        print(f"   • الضغط الكلي المتوقع: {total_pressure:.2f} bar")
        
        # الإجهادات
        print("\n🔧 تحليل الإجهادات:")
        print(f"   • إجهاد الطوق (Hoop Stress): {analysis['hoop_stress']/1e6:.2f} MPa")
        print(f"   • مقاومة الخضوع للمادة: {pipe.yield_strength/1e6:.2f} MPa")
        
        # عامل الأمان
        safety_factor = analysis['safety_factor']
        safety_color = "🟢" if safety_factor > 2.0 else "🟡" if safety_factor > 1.5 else "🔴"
        print(f"   • عامل الأمان: {safety_color} {safety_factor:.2f}")
        
        if safety_factor < 1.5:
            print("   ⚠️ تحذير: عامل الأمان منخفض جداً! خطر فشل الأنبوب مرتفع!")
        
        # التوصيات
        print("\n💡 التوصيات والإجراءات المقترحة:")
        print("-"*60)
        for i, rec in enumerate(recommendations, 1):
            print(f"   {rec}")
        
        # ملخص تنفيذي
        print("\n" + "="*80)
        print("                    📋 ملخص تنفيذي")
        print("="*80)
        print(f"""
        النظام تحت تحليل:
        • أنبوب بطول {pipe.length:.1f} متر وقطر {pipe.diameter*1000:.0f} مم
        • سرعة تدفق {analysis['velocity_change']:.2f} m/s
        • ضغط تشغيل {operating_pressure_bar:.1f} bar
        
        المطرقة المائية المتوقعة:
        • ضغط إضافي: {analysis['delta_pressure_bar']:.2f} bar
        • ضغط كلي: {total_pressure:.2f} bar
        • زمن حرج: {analysis['critical_time']:.3f} ثانية
        
        تقييم السلامة: {'✅ آمن' if safety_factor > 2.0 else '⚠️ يحتاج تحسين' if safety_factor > 1.5 else '❌ خطر'}
        """)
        
        # رسوم بيانية بسيطة (نصية)
        print("\n📊 تمثيل بياني للضغوط:")
        print("-"*40)
        max_scale = max(total_pressure, 50)
        scale_factor = 30 / max_scale
        
        op_bar = int(operating_pressure_bar * scale_factor)
        delta_bar = int(analysis['delta_pressure_bar'] * scale_factor)
        
        print("ضغط التشغيل:  " + "█" * op_bar + f" {operating_pressure_bar:.1f} bar")
        print("ضغط المطرقة:  " + "█" * delta_bar + f" {analysis['delta_pressure_bar']:.1f} bar")
        print("الضغط الكلي:   " + "█" * (op_bar + delta_bar) + f" {total_pressure:.1f} bar")
        print("-"*40)

def main():
    """الوظيفة الرئيسية للبرنامج"""
    
    ui = UserInterface()
    analyzer = WaterHammerAnalyzer()
    
    try:
        # عرض رأس البرنامج
        ui.print_header()
        
        print("📝 الرجاء إدخال بيانات النظام:\n")
        
        # إدخال بيانات الأنبوب
        print("-"*60)
        print("🔧 بيانات الأنبوب:")
        pipe_length = ui.get_float_input("طول الأنبوب", min_val=0.1, max_val=10000, 
                                        unit="m", default=100.0)
        pipe_diameter = ui.get_float_input("قطر الأنبوب الداخلي", min_val=0.01, max_val=5.0,
                                          unit="m", default=0.3)
        wall_thickness = ui.get_float_input("سماكة جدار الأنبوب", min_val=0.001, max_val=0.1,
                                           unit="m", default=0.01)
        
        # اختيار مادة الأنبوب
        material = ui.select_pipe_material()
        material_name, E_modulus, poisson, yield_strength = material.value
        
        print(f"\n✅ تم اختيار: {material_name}")
        
        # إدخال بيانات السائل
        print("\n" + "-"*60)
        print("💧 بيانات المائع:")
        fluid_density = ui.get_float_input("كثافة الماء", min_val=900, max_val=1100,
                                          unit="kg/m³", default=1000.0)
        flow_velocity = ui.get_float_input("سرعة تدفق الماء", min_val=0.1, max_val=20.0,
                                          unit="m/s", default=2.0)
        
        # إدخال بيانات التشغيل
        print("\n" + "-"*60)
        print("⚙️ بيانات التشغيل:")
        operating_pressure = ui.get_float_input("ضغط التشغيل الأساسي", min_val=1, max_val=100,
                                               unit="bar", default=5.0)
        closure_time = ui.get_float_input("زمن إغلاق الصمام", min_val=0.01, max_val=60.0,
                                         unit="seconds", default=1.0)
        
        # إنشاء كائنات البيانات
        pipe = PipeParameters(
            length=pipe_length,
            diameter=pipe_diameter,
            wall_thickness=wall_thickness,
            elastic_modulus=E_modulus,
            poisson_ratio=poisson,
            yield_strength=yield_strength
        )
        
        fluid = FluidProperties(
            density=fluid_density
        )
        
        # إجراء التحليل
        print("\n" + "="*80)
        print("⏳ جاري إجراء التحليل الهندسي...")
        print("="*80)
        
        analysis_results = analyzer.analyze_valve_closure(
            pipe, fluid, flow_velocity, closure_time
        )
        
        # الحصول على التوصيات
        recommendations = analyzer.get_mitigation_recommendations(
            analysis_results, operating_pressure
        )
        
        # عرض النتائج
        ui.display_results(analysis_results, pipe, fluid, operating_pressure, recommendations)
        
        # خيار تصدير النتائج
        export = input("\n📁 هل تريد تصدير النتائج إلى ملف؟ (y/n): ").strip().lower()
        if export == 'y':
            filename = input("اسم الملف (بدون امتداد): ").strip()
            if not filename:
                filename = "water_hammer_analysis"
            
            export_results = {
                'pipe_parameters': {
                    'length_m': pipe.length,
                    'diameter_m': pipe.diameter,
                    'wall_thickness_m': pipe.wall_thickness,
                    'material': material_name,
                    'elastic_modulus_pa': pipe.elastic_modulus,
                    'yield_strength_pa': pipe.yield_strength
                },
                'fluid_parameters': {
                    'density_kgm3': fluid.density,
                    'velocity_ms': flow_velocity
                },
                'operating_conditions': {
                    'pressure_bar': operating_pressure,
                    'closure_time_s': closure_time
                },
                'results': analysis_results,
                'recommendations': recommendations
            }
            
            with open(f"{filename}.json", 'w', encoding='utf-8') as f:
                json.dump(export_results, f, indent=2, ensure_ascii=False)
            print(f"✅ تم تصدير النتائج إلى {filename}.json")
        
        print("\n" + "="*80)
        print("🙏 شكراً لاستخدامك أداة تحليل المطرقة المائية الاحترافية")
        print("="*80 + "\n")
        
    except KeyboardInterrupt:
        print("\n\n⚠️ تم إيقاف البرنامج من قبل المستخدم")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ حدث خطأ غير متوقع: {str(e)}")
        print("الرجاء التحقق من البيانات المدخلة وإعادة المحاولة")
        sys.exit(1)

if __name__ == "__main__":
    main()