# 圣石选择.py
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context 
# 最终修正：从 'maa.define' 导入 RecognitionDetail, OCRResult, Rect
from maa.define import RecognitionDetail, OCRResult, Rect # type: ignore # 加上 type: ignore 暂时忽略Pylance警告

import sys
import re
from typing import Dict, Union, List, Optional # 导入必要的类型提示，保持代码规范
import numpy # context.run_recognition 的 image 参数需要 numpy.ndarray

@AgentServer.custom_recognition("material_selector")
class MaterialSelectorRecognition(CustomRecognition):
    
    # 将 FAIL_VALUE 定义为类的常量，方便访问
    FAIL_VALUE = 9999999

    def _extract_number_from_result(self, reco_detail_obj: RecognitionDetail, recognizer_name: str = "__Internal_Python_OCR__") -> int:
        """
        从 RecognitionDetail 对象中提取数字。
        这个版本根据 MaaFramework Python 绑定源码，从 RecognitionDetail.best_result.text (类型为 OCRResult) 获取文本。
        """
        raw_text = ""
        cleaned_text = ""
        
        try:
            if reco_detail_obj is None:
                print(f"DEBUG: '{recognizer_name}' 识别结果 RecognitionDetail 对象为 None。", file=sys.stderr)
                return self.FAIL_VALUE
            
            # 打印调试信息，确认 reco_detail_obj 的基础结构
            print(f"DEBUG: reco_detail_obj 对象类型: {type(reco_detail_obj)}", file=sys.stderr)
            print(f"DEBUG: reco_detail_obj 对象所有属性: {dir(reco_detail_obj)}", file=sys.stderr)

            # 核心修正：从 RecognitionDetail.best_result.text 中提取文本
            # 这里的 best_result 实际类型会是 OCRResult (因为我们运行的是 OCR 识别)
            if hasattr(reco_detail_obj, 'best_result') and reco_detail_obj.best_result is not None:
                best_ocr_result: OCRResult = reco_detail_obj.best_result # 类型提示为OCRResult
                if hasattr(best_ocr_result, 'text') and best_ocr_result.text is not None:
                    raw_text = str(best_ocr_result.text)
                    print(f"DEBUG: 成功从 reco_detail_obj.best_result.text 获取原始文本: '{raw_text}'", file=sys.stderr)
                else:
                    print("DEBUG: reco_detail_obj.best_result.text 为 None 或不存在。", file=sys.stderr)
            else:
                print("DEBUG: reco_detail_obj 没有 'best_result' 属性或其值为 None。", file=sys.stderr)
                
                # 备用方案：如果 best_result 为空，尝试从 all_results 中获取第一个 OCRResult 的文本
                if hasattr(reco_detail_obj, 'all_results') and isinstance(reco_detail_obj.all_results, list) and len(reco_detail_obj.all_results) > 0:
                    first_result = reco_detail_obj.all_results[0]
                    if isinstance(first_result, OCRResult) and hasattr(first_result, 'text') and first_result.text is not None:
                        raw_text = str(first_result.text)
                        print(f"DEBUG: 成功从 reco_detail_obj.all_results[0].text 获取原始文本 (备用): '{raw_text}'", file=sys.stderr)
                    else:
                        print("DEBUG: all_results 中第一个结果不是 OCRResult 或其文本为 None。", file=sys.stderr)
                else:
                    print("DEBUG: reco_detail_obj.all_results 为空或不是列表。", file=sys.stderr)


            if not raw_text:
                print("DEBUG: 最终提取到的原始文本为空，无法转换为数字。", file=sys.stderr)
                return self.FAIL_VALUE

            # 2. 清理文本：移除所有非数字字符，特别是逗号
            if isinstance(raw_text, str):
                cleaned_text = re.sub(r'[^\d]', '', raw_text)
            else:
                print(f"DEBUG: 原始文本'{raw_text}'类型为 {type(raw_text)}，不是字符串类型，无法清理。", file=sys.stderr)
                return self.FAIL_VALUE

            print(f"清理逗号及其他非数字字符后: '{cleaned_text}'", file=sys.stderr)

            # 3. 将清理后的字符串转换为数字
            if cleaned_text:
                number = int(cleaned_text)
                print(f"成功解析出数字: {number}", file=sys.stderr)
                return number
            else:
                print(f"在清理后的文本'{cleaned_text}'中未找到任何有效数字。", file=sys.stderr)
                return self.FAIL_VALUE
                
        except (ValueError, TypeError) as e:
            print(f"ERROR: 将原始文本'{raw_text}'，清理后'{cleaned_text}' 转换为数字失败: {e}", file=sys.stderr)
            return self.FAIL_VALUE
        except Exception as e:
            print(f"CRITICAL ERROR: 提取数字过程中发生未知错误 (原始文本: '{raw_text}', 清理后: '{cleaned_text}'): {e}", file=sys.stderr)
            return self.FAIL_VALUE

    def _detect_material_count(self, context: Context, image: numpy.ndarray, roi: List[int]) -> int:
        """
        通用的材料数量检测函数。
        使用 context.run_recognition 方法。
        """
        try:
            node_to_run = "__Internal_Python_OCR__"
            
            print(f"DEBUG: 准备调用 context.run_recognition for ROI: {roi}", file=sys.stderr)
            
            # 核心修正：context.run_recognition 直接返回 Optional[RecognitionDetail]
            reco_detail_from_run_recognition: Optional[RecognitionDetail] = context.run_recognition(
                node_to_run,
                image,
                pipeline_override={
                    node_to_run: {
                        "recognition": "OCR",
                        "roi": roi,
                        "method": "Default", 
                        "pre_process": [
                            {"type": "Gray"},
                            {"type": "Threshold", "threshold": 180}
                        ]
                    }
                }
            )
            
            if reco_detail_from_run_recognition is None:
                print(f"DEBUG: context.run_recognition for ROI {roi} 返回 None。", file=sys.stderr)
                return self.FAIL_VALUE

            # 直接将获取到的 RecognitionDetail 对象传递给 _extract_number_from_result
            # 同时 _extract_number_from_result 的第一个参数也需要从 Dict[str, RecognitionDetail] 调整为 RecognitionDetail
            print(f"DEBUG: context.run_recognition 返回值类型: {type(reco_detail_from_run_recognition)}", file=sys.stderr)
            print(f"DEBUG: context.run_recognition 返回值内容: {reco_detail_from_run_recognition}", file=sys.stderr)

            return self._extract_number_from_result(reco_detail_from_run_recognition, node_to_run)
            
        except Exception as e:
            print(f"ERROR: ROI {roi} 的材料识别任务执行失败: {e}", file=sys.stderr)
            return self.FAIL_VALUE

    def analyze(
        self,
        context: Context,
        argv: CustomRecognition.AnalyzeArg,
    ) -> CustomRecognition.AnalyzeResult:
        """主分析函数，负责调度识别并做出决策"""
        print("--- 开始执行圣石材料数量检测与选择 ---", file=sys.stderr)
        
        try:
            material_definitions = [
                {"name": "火", "roi": [1120, 55, 73, 23],  "task": "快速狩猎_圣石洞穴_火材料选择"},
                {"name": "水", "roi": [1120, 83, 73, 23],  "task": "快速狩猎_圣石洞穴_水材料选择"},
                {"name": "风", "roi": [1120, 111, 73, 23], "task": "快速狩猎_圣石洞穴_风材料选择"},
                {"name": "光", "roi": [1120, 139, 73, 23], "task": "快速狩猎_圣石洞穴_光材料选择"},
                {"name": "暗", "roi": [1120, 167, 73, 23], "task": "快速狩猎_圣石洞穴_暗材料选择"}
            ]

            material_counts = []

            for mat in material_definitions:
                count = self._detect_material_count(context, argv.image, mat["roi"])
                material_counts.append({"name": mat["name"], "count": count, "task": mat["task"]})
                print(f"检测到 {mat['name']} 材料数量: {count}", file=sys.stderr)
            
            valid_materials = [m for m in material_counts if m["count"] < self.FAIL_VALUE] # 使用类的常量
            
            if not valid_materials:
                print("警告：所有材料数量识别失败！执行默认操作。", file=sys.stderr)
                chosen_material = {"name": "风(默认)", "task": "快速狩猎_圣石洞穴_风材料选择"}
            else:
                min_material = min(valid_materials, key=lambda x: x["count"])
                chosen_material = {"name": f"{min_material['name']}(最少)", "task": min_material['task']}

            print(f"最终决定：选择 {chosen_material['name']}。即将跳转到任务: {chosen_material['task']}", file=sys.stderr)
            
            context.override_next(argv.node_name, [chosen_material['task']])
            
            return CustomRecognition.AnalyzeResult(
                box=(0, 0, 0, 0), detail=f"选择 {chosen_material['name']}"
            )
            
        except Exception as e:
            print(f"!!! CRITICAL ERROR: 在材料选择主逻辑中发生严重错误: {e}", file=sys.stderr)
            default_task = "快速狩猎_圣石洞穴_风材料选择"
            context.override_next(argv.node_name, [default_task])
            return CustomRecognition.AnalyzeResult(box=(0, 0, 0, 0), detail=f"出错,默认选择风材料")
