# 圣石选择.py
from maa.agent.agent_server import AgentServer
from maa.custom_recognition import CustomRecognition
from maa.context import Context 
from maa.define import RecognitionDetail, OCRResult, Rect # type: ignore 

import sys
import re
from typing import Dict, Union, List, Optional
import numpy

@AgentServer.custom_recognition("material_selector")
class MaterialSelectorRecognition(CustomRecognition):
    
    FAIL_VALUE = 9999999

    def _extract_number_from_result(self, reco_detail_obj: RecognitionDetail, recognizer_name: str = "__Internal_Python_OCR__") -> int:
        # （此函数保持不变）
        raw_text = ""
        cleaned_text = ""
        
        try:
            if reco_detail_obj is None:
                print(f"DEBUG: '{recognizer_name}' 识别结果 RecognitionDetail 对象为 None。", file=sys.stderr)
                return self.FAIL_VALUE
            
            # print(f"DEBUG: reco_detail_obj 对象类型: {type(reco_detail_obj)}", file=sys.stderr)
            # print(f"DEBUG: reco_detail_obj 对象所有属性: {dir(reco_detail_obj)}", file=sys.stderr)

            if hasattr(reco_detail_obj, 'best_result') and reco_detail_obj.best_result is not None:
                best_ocr_result: OCRResult = reco_detail_obj.best_result
                if hasattr(best_ocr_result, 'text') and best_ocr_result.text is not None:
                    raw_text = str(best_ocr_result.text)
                    #print(f"DEBUG: 成功从 reco_detail_obj.best_result.text 获取原始文本: '{raw_text}'", file=sys.stderr)
                else:
                    print("DEBUG: reco_detail_obj.best_result.text 为 None 或不存在。", file=sys.stderr)
            else:
                print("DEBUG: reco_detail_obj 没有 'best_result' 属性或其值为 None。", file=sys.stderr)
                
                if hasattr(reco_detail_obj, 'all_results') and isinstance(reco_detail_obj.all_results, list) and len(reco_detail_obj.all_results) > 0:
                    first_result = reco_detail_obj.all_results[0]
                    if isinstance(first_result, OCRResult) and hasattr(first_result, 'text') and first_result.text is not None:
                        raw_text = str(first_result.text)
                        #print(f"DEBUG: 成功从 reco_detail_obj.all_results[0].text 获取原始文本 (备用): '{raw_text}'", file=sys.stderr)
                    else:
                        print("DEBUG: all_results 中第一个结果不是 OCRResult 或其文本为 None。", file=sys.stderr)
                else:
                    print("DEBUG: reco_detail_obj.all_results 为空或不是列表。", file=sys.stderr)


            if not raw_text:
                print("DEBUG: 最终提取到的原始文本为空，无法转换为数字。", file=sys.stderr)
                return self.FAIL_VALUE

            if isinstance(raw_text, str):
                cleaned_text = re.sub(r'[^\d]', '', raw_text)
            else:
                print(f"DEBUG: 原始文本'{raw_text}'类型为 {type(raw_text)}，不是字符串类型，无法清理。", file=sys.stderr)
                return self.FAIL_VALUE

            #print(f"清理逗号及其他非数字字符后: '{cleaned_text}'", file=sys.stderr)

            if cleaned_text:
                number = int(cleaned_text)
                #print(f"成功解析出数字: {number}", file=sys.stderr)
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
        # （此函数保持不变）
        try:
            node_to_run = "__Internal_Python_OCR__"
            
            #print(f"DEBUG: 准备调用 context.run_recognition for ROI: {roi}", file=sys.stderr)
            
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

            # print(f"DEBUG: context.run_recognition 返回值类型: {type(reco_detail_from_run_recognition)}", file=sys.stderr)
            # print(f"DEBUG: context.run_recognition 返回值内容: {reco_detail_from_run_recognition}", file=sys.stderr)

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
        
        selected_material_type = None
        
        # --- 修正点在这里！强制将 custom_recognition_param 解析为字典 ---
        processed_params = {}
        if argv.custom_recognition_param:
            try:
                # 假设它可能是一个 JSON 字符串，尝试解析
                if isinstance(argv.custom_recognition_param, str):
                    import json
                    processed_params = json.loads(argv.custom_recognition_param)
                    print(f"DEBUG: 成功将 custom_recognition_param 字符串解析为字典: {processed_params}", file=sys.stderr)
                # 如果它已经是字典，直接使用
                elif isinstance(argv.custom_recognition_param, dict):
                    processed_params = argv.custom_recognition_param
                    print(f"DEBUG: custom_recognition_param 已经是字典: {processed_params}", file=sys.stderr)
                else:
                    print(f"WARNING: custom_recognition_param 类型未知: {type(argv.custom_recognition_param)}，无法处理。", file=sys.stderr)
            except json.JSONDecodeError as e:
                print(f"ERROR: 解析 custom_recognition_param JSON 字符串失败: {e}", file=sys.stderr)
            except Exception as e:
                print(f"CRITICAL ERROR: 处理 custom_recognition_param 时发生未知错误: {e}", file=sys.stderr)
        # 现在使用 processed_params 替代 argv.custom_recognition_param
        if processed_params and "selected_material_type" in processed_params:
            selected_material_type = processed_params["selected_material_type"]
            print(f"DEBUG: 从 GUI 接收到用户选择的材料类型 (已处理): '{selected_material_type}'", file=sys.stderr)
        else:
            print("DEBUG: 未从 GUI 接收到用户选择的材料类型，或参数为空/无效。", file=sys.stderr)
        # --- 修正点结束 ---
        try:
            material_definitions = [
                {"name": "火", "roi": [1120, 55, 73, 23],  "task": "快速狩猎_圣石洞穴_火材料选择"},
                {"name": "水", "roi": [1120, 83, 73, 23],  "task": "快速狩猎_圣石洞穴_水材料选择"},
                {"name": "风", "roi": [1120, 111, 73, 23], "task": "快速狩猎_圣石洞穴_风材料选择"},
                {"name": "光", "roi": [1120, 139, 73, 23], "task": "快速狩猎_圣石洞穴_光材料选择"},
                {"name": "暗", "roi": [1120, 167, 73, 23], "task": "快速狩猎_圣石洞穴_暗材料选择"} 
            ]
            chosen_material = None
            
            if selected_material_type and selected_material_type != "min":
                for mat_def in material_definitions:
                    if mat_def["name"] == selected_material_type:
                        chosen_material = {"name": f"{mat_def['name']}(用户指定)", "task": mat_def['task']}
                        print(f"DEBUG: 用户指定选择材料: {mat_def['name']}", file=sys.stderr)
                        break
                if chosen_material is None:
                    print(f"警告：用户指定材料 '{selected_material_type}' 未在定义中找到。将回退到自动选择最少。", file=sys.stderr)
            
            if chosen_material is None: 
                print("DEBUG: 未指定材料或指定为'min'，开始识别所有材料数量。", file=sys.stderr)
                material_counts = []
                for mat in material_definitions:
                    count = self._detect_material_count(context, argv.image, mat["roi"])
                    material_counts.append({"name": mat["name"], "count": count, "task": mat["task"]})
                    print(f"检测到 {mat['name']} 材料数量: {count}", file=sys.stderr)
                
                valid_materials = [m for m in material_counts if m["count"] < self.FAIL_VALUE]
                
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