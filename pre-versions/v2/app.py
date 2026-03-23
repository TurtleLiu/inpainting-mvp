import streamlit as st
from PIL import Image
import io
import os
import numpy as np
from datetime import datetime
from src.inpainting_app.service import InpaintingService
from src.inpainting_app.auth import AuthService
from src.inpainting_app.sam_mask import grabcut_mask

st.set_page_config(page_title="图像缺损区域重建应用", layout="wide")
st.title("🖼️ 图像缺损区域重建应用")
st.caption("基于 Streamlit 的图像修复 MVP 应用")

auth_service = AuthService()
service = InpaintingService()

if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.username = None
    st.session_state.history = []

with st.sidebar:
    st.header("账号管理")
    if not st.session_state.authenticated:
        username = st.text_input("用户名", value="demo")
        password = st.text_input("密码", value="demo123", type="password")
        if st.button("登录"):
            if auth_service.authenticate(username, password):
                st.session_state.authenticated = True
                st.session_state.username = username
                st.success("登录成功！")
                st.rerun()
            else:
                st.error("用户名或密码错误")
    else:
        st.write(f"当前用户: {st.session_state.username}")
        if st.button("退出登录"):
            st.session_state.authenticated = False
            st.session_state.username = None
            st.rerun()

if not st.session_state.authenticated:
    st.info("请先登录系统")
    st.stop()

tab1, tab2, tab3 = st.tabs(["单图修复", "批量修复", "任务历史"])

with tab1:
    st.subheader("单图修复")
    col1, col2 = st.columns(2)
    
    with col1:
        image_file = st.file_uploader("上传原图", type=["png", "jpg", "jpeg"], key="single_image")
        mask_mode = st.radio("Mask方式", ["手动上传", "自动生成"], horizontal=True)
        
        if mask_mode == "手动上传":
            mask_file = st.file_uploader("上传Mask", type=["png", "jpg", "jpeg"], key="single_mask")
        else:
            st.markdown("### 自动生成Mask")
            
            if image_file:
                img = Image.open(image_file)
                width, height = img.size
                
                mask_width = int(width * 0.3)
                mask_height = int(height * 0.4)
                
                default_x1 = width // 2 + width // 6
                default_y1 = height // 2 - mask_height // 2
                default_x2 = default_x1 + mask_width
                default_y2 = default_y1 + mask_height
            else:
                default_x1, default_y1, default_x2, default_y2 = 10, 10, 100, 100
            
            x1 = st.number_input("x1", min_value=0, max_value=4000, value=default_x1)
            y1 = st.number_input("y1", min_value=0, max_value=4000, value=default_y1)
            x2 = st.number_input("x2", min_value=1, max_value=4000, value=default_x2)
            y2 = st.number_input("y2", min_value=1, max_value=4000, value=default_y2)
        
        method = st.selectbox("修复算法", ["telea", "navier-stokes"], index=0)
        
        if st.button("开始修复"):
            if not image_file:
                st.error("请上传图片")
            elif mask_mode == "手动上传" and not mask_file:
                st.error("请上传Mask")
            else:
                try:
                    with st.spinner("正在修复..."):
                        image_bytes = image_file.getvalue()
                        
                        if mask_mode == "手动上传":
                            mask_bytes = mask_file.getvalue()
                        else:
                            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
                            mask = grabcut_mask(img, (x1, y1, x2, y2))
                            mask_buf = io.BytesIO()
                            mask.save(mask_buf, format="PNG")
                            mask_bytes = mask_buf.getvalue()
                        
                        result = service.process_image_from_bytes(
                            image_bytes=image_bytes,
                            mask_bytes=mask_bytes,
                            backend="opencv",
                            method=method
                        )
                        
                        st.success("修复完成！")
                        
                        with col2:
                            st.subheader("修复结果")
                            st.image(result, caption="修复后的图片", use_container_width=True)
                            
                            buf = io.BytesIO()
                            result.save(buf, format="PNG")
                            buf.seek(0)
                            
                            st.download_button(
                                label="下载修复结果",
                                data=buf,
                                file_name=f"inpainting_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png",
                                mime="image/png"
                            )
                        
                        st.session_state.history.append({
                            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            "type": "single",
                            "filename": image_file.name,
                            "method": method,
                            "mask_mode": mask_mode,
                            "result": result
                        })
                        
                except Exception as e:
                    st.error(f"修复失败: {str(e)}")
    
    if image_file:
        with col2:
            st.subheader("原图预览")
            img = Image.open(image_file)
            st.image(img, caption="原图", use_container_width=True)
            
            if mask_mode == "自动生成" and st.button("预览自动Mask"):
                img = Image.open(io.BytesIO(image_file.getvalue())).convert("RGB")
                mask = grabcut_mask(img, (x1, y1, x2, y2))
                
                gray_img = img.convert('L').convert('RGB')
                
                mask_array = np.array(mask)
                img_array = np.array(gray_img)
                img_array[mask_array == 255] = [255, 255, 255]
                
                preview_img = Image.fromarray(img_array)
                
                st.subheader("自动生成的Mask预览")
                st.image(preview_img, caption="黑白照片+白色遮挡", use_container_width=True)
    
    if mask_mode == "手动上传" and mask_file:
        with col2:
            st.subheader("Mask预览")
            mask = Image.open(mask_file)
            st.image(mask, caption="Mask", use_container_width=True)

with tab2:
    st.subheader("批量修复")
    images = st.file_uploader("批量上传原图", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="batch_images")
    masks = st.file_uploader("批量上传对应Mask", type=["png", "jpg", "jpeg"], accept_multiple_files=True, key="batch_masks")
    method = st.selectbox("修复算法", ["telea", "navier-stokes"], index=0, key="batch_method")
    
    if st.button("开始批量修复"):
        if not images or not masks:
            st.error("请上传图片和对应的Mask")
        elif len(images) != len(masks):
            st.error("图片和Mask数量必须一致")
        else:
            try:
                results = []
                with st.spinner("正在批量修复..."):
                    for i, (image_file, mask_file) in enumerate(zip(images, masks)):
                        st.write(f"正在处理第 {i+1}/{len(images)} 张图片: {image_file.name}")
                        image_bytes = image_file.getvalue()
                        mask_bytes = mask_file.getvalue()
                        
                        result = service.process_image_from_bytes(
                            image_bytes=image_bytes,
                            mask_bytes=mask_bytes,
                            backend="opencv",
                            method=method
                        )
                        results.append((image_file.name, result))
                
                st.success(f"批量修复完成！共处理 {len(results)} 张图片")
                
                for filename, result in results:
                    st.subheader(f"结果: {filename}")
                    st.image(result, caption=f"修复后的图片: {filename}", use_container_width=True)
                    
                    buf = io.BytesIO()
                    result.save(buf, format="PNG")
                    buf.seek(0)
                    
                    st.download_button(
                        label=f"下载 {filename} 的修复结果",
                        data=buf,
                        file_name=f"inpainting_result_{os.path.splitext(filename)[0]}.png",
                        mime="image/png",
                        key=f"download_{filename}"
                    )
                
                st.session_state.history.append({
                    "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    "type": "batch",
                    "count": len(images),
                    "method": method,
                    "results": results
                })
                
            except Exception as e:
                st.error(f"批量修复失败: {str(e)}")

with tab3:
    st.subheader("任务历史")
    if not st.session_state.history:
        st.info("暂无任务记录")
    else:
        for i, task in enumerate(reversed(st.session_state.history)):
            with st.expander(f"任务 {i+1} | {task['timestamp']} | {task['type']}"):
                if task['type'] == 'single':
                    st.write(f"文件名: {task['filename']}")
                    st.write(f"修复算法: {task['method']}")
                    st.write(f"Mask方式: {task['mask_mode']}")
                    st.image(task['result'], caption="修复结果", use_container_width=True)
                    
                    buf = io.BytesIO()
                    task['result'].save(buf, format="PNG")
                    buf.seek(0)
                    
                    st.download_button(
                        label="下载结果",
                        data=buf,
                        file_name=f"history_result_{i+1}.png",
                        mime="image/png",
                        key=f"history_download_{i}"
                    )
                else:
                    st.write(f"批量处理: {task['count']} 张图片")
                    st.write(f"修复算法: {task['method']}")
                    for j, (filename, result) in enumerate(task['results']):
                        st.subheader(f"{filename}")
                        st.image(result, caption=f"修复结果: {filename}", use_container_width=True)
                        
                        buf = io.BytesIO()
                        result.save(buf, format="PNG")
                        buf.seek(0)
                        
                        st.download_button(
                            label=f"下载 {filename}",
                            data=buf,
                            file_name=f"history_batch_{i+1}_{j+1}.png",
                            mime="image/png",
                            key=f"history_batch_download_{i}_{j}"
                        )