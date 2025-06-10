
import streamlit as st
import requests
import os
from io import BytesIO
import base64

# Configuration
API_CHOICES = {
    "Stable Diffusion": "stability",
    "DALL·E (OpenAI)": "dalle"
}

# API Key Setup
def setup_api_keys():
    if 'api_keys' not in st.session_state:
        st.session_state.api_keys = {
            "stability": os.getenv("STABILITY_API_KEY", ""),
            "dalle": os.getenv("OPENAI_API_KEY", "")
        }

# Generate prompts
def generate_prompt(keywords, style, quality, lighting, artist, negative):
    prompt = f"{quality} {style} style {keywords}"
    if lighting != "None":
        prompt += f", {lighting} lighting"
    if artist:
        prompt += f", in the style of {artist}"
    return prompt

# API Call Functions
def generate_with_stability(prompt, negative_prompt, width=512, height=512):
    api_key = st.session_state.api_keys["stability"]
    if not api_key:
        st.error("Stability API key not configured")
        return None
    
    engine_id = "stable-diffusion-xl-1024-v1-0"
    api_host = "https://api.stability.ai"
    
    response = requests.post(
        f"{api_host}/v1/generation/{engine_id}/text-to-image",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        json={
            "text_prompts": [
                {
                    "text": prompt,
                    "weight": 1
                },
                {
                    "text": negative_prompt,
                    "weight": -1
                }
            ],
            "cfg_scale": 7,
            "height": height,
            "width": width,
            "samples": 1,
            "steps": 30,
        },
    )
    
    if response.status_code == 200:
        data = response.json()
        return data["artifacts"][0]["base64"]
    else:
        st.error(f"API Error: {response.text}")
        return None

def generate_with_dalle(prompt, size="1024x1024"):
    api_key = st.session_state.api_keys["dalle"]
    if not api_key:
        st.error("OpenAI API key not configured")
        return None
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    
    payload = {
        "model": "dall-e-3",
        "prompt": prompt,
        "n": 1,
        "size": size,
        "quality": "standard"
    }
    
    try:
        response = requests.post(
            "https://api.openai.com/v1/images/generations",
            headers=headers,
            json=payload
        )
        response.raise_for_status()
        image_url = response.json()["data"][0]["url"]
        image_response = requests.get(image_url)
        return base64.b64encode(image_response.content).decode('utf-8')
    except Exception as e:
        st.error(f"API Error: {str(e)}")
        return None

# Streamlit UI
def main():
    st.set_page_config(page_title="AI Image Generator", layout="wide")
    st.title("🖼️ AI Image Generator")
    
    setup_api_keys()
    
    # Sidebar for API configuration
    with st.sidebar:
        st.header("API Configuration")
        api_choice = st.radio("Select API:", list(API_CHOICES.keys()))
        
        if api_choice == "Stable Diffusion":
            st.session_state.api_keys["stability"] = st.text_input(
                "Stability API Key",
                value=st.session_state.api_keys["stability"],
                type="password"
            )
        else:
            st.session_state.api_keys["dalle"] = st.text_input(
                "OpenAI API Key",
                value=st.session_state.api_keys["dalle"],
                type="password"
            )
        
        st.divider()
        st.header("Image Settings")
        width = st.slider("Width", 256, 1024, 512, 64)
        height = st.slider("Height", 256, 1024, 512, 64)
    
    # Main content
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("Prompt Parameters")
        keywords = st.text_input("Main Keywords:", placeholder="A majestic lion in the savannah")
        
        style = st.selectbox("Art Style:", ["Realistic", "Oil Painting", "Anime", 
                                          "Watercolor", "Cyberpunk", "Pixel Art", 
                                          "Surrealist", "Renaissance"])
        
        quality = st.select_slider("Quality Level:", 
                                  options=["Low", "Medium", "High", "Ultra HD"])
        
        lighting = st.radio("Lighting:", ["None", "Cinematic", "Golden Hour", 
                                        "Neon", "Studio", "Moody"])
        
        artist = st.text_input("Artist Style (optional):", placeholder="e.g., Van Gogh, Studio Ghibli")
        
        negative = st.text_area("Negative Prompts:", 
                               placeholder="Things to avoid (blurry, deformed hands, text...)",
                               height=100)
        
        if st.button("Generate Image", type="primary", use_container_width=True):
            with st.spinner("Generating image..."):
                # Generate prompt
                final_prompt = generate_prompt(keywords, style, quality, lighting, artist, negative)
                st.session_state.final_prompt = final_prompt
                
                # Call appropriate API
                if API_CHOICES[api_choice] == "stability":
                    image_data = generate_with_stability(
                        final_prompt, 
                        negative,
                        width=width,
                        height=height
                    )
                else:
                    image_data = generate_with_dalle(
                        final_prompt,
                        size=f"{width}x{height}"
                    )
                
                if image_data:
                    st.session_state.generated_image = image_data
                    st.session_state.generated = True
    
    with col2:
        st.subheader("Generated Image")
        
        if 'generated' in st.session_state:
            st.code(st.session_state.final_prompt, language="text")
            
            # Display generated image
            image_bytes = base64.b64decode(st.session_state.generated_image)
            
            col2a, col2b = st.columns(2)
            with col2a:
                st.image(image_bytes, caption="Generated Image", use_column_width=True)
            
            with col2b:
                st.download_button(
                    label="Download Image",
                    data=image_bytes,
                    file_name="generated_image.png",
                    mime="image/png",
                    use_container_width=True
                )
                
                st.download_button(
                    label="Copy Prompt",
                    data=st.session_state.final_prompt,
                    file_name="ai_prompt.txt",
                    mime="text/plain",
                    use_container_width=True
                )
        else:
            st.info("Enter parameters and click 'Generate Image'")

if __name__ == "__main__":
    main()
