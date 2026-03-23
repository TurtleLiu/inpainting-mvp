
import sys
import os
from pathlib import Path
import io
import streamlit as st
from PIL import Image, ImageOps

sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from inpainting_app.service import InpaintingService
from inpainting_app.security import validate_upload, validate_mask
from inpainting_app.config import AppConfig

st.set_page_config(page_title="图像缺损区域重建 MVP", page_icon="🖼️", layout="wide")

cfg = AppConfig()
service = InpaintingService(cfg)

st.title("图像缺损区域重建 MVP")
st.caption("基于 Streamlit + 可替换推理后端的图像修复应用。默认使用 OpenCV 作为可运行基线，并预留 AI 模型接入位。")

with st.sidebar:
    st.header("参数")
    algorithm = st.selectbox("修复算法", ["telea", "ns"], index=0, help="MVP 默认使用 OpenCV inpaint；后续可替换为 LaMa / Diffusers Inpainting。")
    radius = st.slider("修复半径", min_value=1, max_value=15, value=3)
    max_edge = st.slider("最大边长", min_value=256, max_value=2048, value=1024, step=128)
    st.markdown("---")
    st.write("**应用场景**")
    st.write("- 商业广告：去水印/去瑕疵")
    st.write("- 影视修复：补全局部缺损")
    st.write("- 老照片修复：裂痕、污点去除")

left, right = st.columns(2)

with left:
    st.subheader("1) 上传原图")
    image_file = st.file_uploader("上传图片", type=["png", "jpg", "jpeg", "webp"])
    st.subheader("2) 上传缺损区域 Mask")
    mask_file = st.file_uploader("上传二值 Mask（白色=待修复区域）", type=["png", "jpg", "jpeg", "webp"])

if image_file and mask_file:
    try:
        img = validate_upload(image_file, cfg)
        mask = validate_mask(mask_file, img.size, cfg)
    except Exception as e:
        st.error(f"输入校验失败：{e}")
        st.stop()

    with left:
        st.image(img, caption="原图", use_container_width=True)
        st.image(mask, caption="Mask", use_container_width=True)

    if st.button("开始修复", type="primary"):
        with st.spinner("正在修复..."):
            result = service.run(img, mask, algorithm=algorithm, radius=radius, max_edge=max_edge)

        with right:
            st.subheader("3) 修复结果")
            st.image(result.output_image, caption="修复结果", use_container_width=True)
            st.write("**处理摘要**")
            st.json(result.meta)

            buf = io.BytesIO()
            result.output_image.save(buf, format="PNG")
            st.download_button(
                "下载结果 PNG",
                data=buf.getvalue(),
                file_name="inpaint_result.png",
                mime="image/png",
            )
else:
    st.info("请先同时上传原图和 Mask。")
