import streamlit as st
import requests
import random
import base64
import os
from io import BytesIO

# Hardcoded API Key (replace with your actual key)
STABILITY_API_KEY = os.getenv("STABILITY_API_KEY"," ")

# Generate prompt with all components
def generate_prompt(keywords, style, quality, lighting, artist, negative):
    components = []
    if quality:
        components.append(quality)
    if style:
        components.append(f"{style} style")
    components.append(keywords)
    if lighting and lighting != "None":
        components.append(f"{lighting} lighting")
    if artist:
        components.append(f"in the style of {artist}")
    
    prompt = ", ".join(components)
    
    if negative:
        negative_prompt = f"Negative: {negative}"
    else:
        negative_prompt = "Negative: None"
    
    return prompt, negative_prompt

# Generate image with Stability Diffusion
def generate_with_stability(prompt, negative_prompt, width=512, height=512):
    if not STABILITY_API_KEY:
        st.error("API key not configured")
        return None
    
    if not prompt or not prompt.strip():
        st.error("Prompt cannot be empty")
        return None
    
    engine_id = "stable-diffusion-xl-1024-v1-0"
    api_host = "https://api.stability.ai"
    
    text_prompts = [{"text": prompt, "weight": 1}]
    if negative_prompt and negative_prompt.lower() != "negative: none":
        text_prompts.append({"text": negative_prompt.replace("Negative: ", ""), "weight": -1})
    
    try:
        response = requests.post(
            f"{api_host}/v1/generation/{engine_id}/text-to-image",
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
                "Authorization": f"Bearer {STABILITY_API_KEY}"
            },
            json={
                "text_prompts": text_prompts,
                "cfg_scale": 7,
                "height": height,
                "width": width,
                "samples": 1,
                "steps": 30,
            },
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return data["artifacts"][0]["base64"]
        else:
            error_msg = response.text
            try:
                error_data = response.json()
                if "message" in error_data:
                    error_msg = error_data["message"]
            except:
                pass
            st.error(f"API Error: {error_msg}")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Network Error: {str(e)}")
        return None

# Main Streamlit UI
def main():
    st.set_page_config(page_title=" General-Purpose AI Image Creator: An Integrated Approach Using Deep Learning and Streamlit", layout="wide")
    st.title("🖼️ Stable Diffusion Image Generator")
    
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Prompt Parameters")
        placeholders = [
    "A majestic lion in the savannah",
    "A serene lake at sunset",
    "A towering mountain peak",
    "A vibrant cityscape at night",
    "A delicate cherry blossom tree",
    "A powerful waterfall cascading down",
    "A stunning aurora borealis display",
    "A peaceful village nestled in the hills",
    "A bustling market filled with colors",
    "A tranquil forest glade",
    "A dramatic thunderstorm rolling in",
    "A beautiful butterfly emerging from its cocoon",
    "A majestic elephant roaming free",
    "A picturesque coastal town",
    "A breathtaking sunrise over the ocean"
]

        
        keywords = st.text_input("Main Subject:", placeholder=random.choice(placeholders), key="keywords")
        
        style = st.selectbox("Art Style:", 
                           ["Realistic", "Oil Painting", "Anime", "Watercolor", 
                            "Cyberpunk", "Pixel Art", "Surrealist", "Renaissance"],
                           key="style")
        
        quality = st.select_slider("Quality Level:", 
                                 options=["Low", "Medium", "High", "Ultra HD"],
                                 value="High",
                                 key="quality")
        
        lighting = st.radio("Lighting:", 
                          ["None", "Cinematic", "Golden Hour", "Neon", "Studio", "Moody"],
                          key="lighting")
        
        artist = st.text_input("Artist Style (optional):", 
                             placeholder="e.g., Van Gogh, Studio Ghibli",
                             key="artist")
        
        negative = st.text_area("Negative Prompts:", 
                              placeholder="Things to avoid (blurry, deformed hands, text...)",
                              height=100,
                              key="negative")
        
        width = st.slider("Width", 512, 1024, 768, 64, key="width")
        height = st.slider("Height", 512, 1024, 768, 64, key="height")
        
        if st.button("Generate Image", type="primary", use_container_width=True):
            if not keywords.strip():
                st.error("Please enter a main subject")
                st.stop()
                
            with st.spinner("Generating image..."):
                prompt, negative_prompt = generate_prompt(
                    keywords.strip(),
                    style,
                    quality,
                    lighting,
                    artist.strip(),
                    negative.strip()
                )
                
                st.session_state.prompt = prompt
                st.session_state.negative_prompt = negative_prompt
                
                image_data = generate_with_stability(
                    prompt,
                    negative_prompt,
                    width=width,
                    height=height
                )
                
                if image_data:
                    st.session_state.generated_image = image_data
                    st.session_state.generated = True
    
    with col2:
        st.subheader("Generated Image")
        
        if 'generated' in st.session_state:
            # Display prompts in expandable sections
            with st.expander("🖋️ PROMPT", expanded=True):
                st.write(st.session_state.prompt)
            
            with st.expander("🚫 NEGATIVE PROMPT", expanded=False):
                st.write(st.session_state.negative_prompt)
            
            # Display image
            image_bytes = base64.b64decode(st.session_state.generated_image)
            st.image(image_bytes, use_container_width=True)
            
            # Download buttons
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="Download Image",
                    data=image_bytes,
                    file_name="generated_image.png",
                    mime="image/png",
                    use_container_width=True
                )
            with col2:
                st.download_button(
                    label="Copy Prompts",
                    data=f"Prompt: {st.session_state.prompt}\n\nNegative Prompt: {st.session_state.negative_prompt}",
                    file_name="prompts.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        else:
            st.info("Enter your prompt parameters and click 'Generate Image'")

if __name__ == "__main__":
    main()
