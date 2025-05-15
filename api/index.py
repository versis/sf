import os
import json
from typing import List, Optional
from openai.types.chat.chat_completion_message_param import ChatCompletionMessageParam
from pydantic import BaseModel
from dotenv import load_dotenv
from fastapi import FastAPI, Query, HTTPException
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from .utils.prompt import ClientMessage, convert_to_openai_messages
from .utils.tools import get_current_weather

import io
import re 
import base64 
from PIL import Image, ImageDraw, ImageFont, ImageOps

load_dotenv(".env.local")

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allows all methods
    allow_headers=["*"],  # Allows all headers
)

client = OpenAI(
    api_key=os.environ.get("OPENAI_API_KEY"),
)


class ChatRequest(BaseModel):
    messages: List[ClientMessage]

# --- Color Conversion Utilities (from shadenfreude) ---
def hex_to_rgb(hex_color: str) -> tuple[int, int, int] | None:
    """Converts a HEX color string to an RGB tuple."""
    hex_color = hex_color.lstrip('#')
    if not re.match(r"^[0-9a-fA-F]{6}$", hex_color) and not re.match(r"^[0-9a-fA-F]{3}$", hex_color):
        print(f"Invalid HEX format: {hex_color}")
        return None 
    
    if len(hex_color) == 3:
        r = int(hex_color[0]*2, 16)
        g = int(hex_color[1]*2, 16)
        b = int(hex_color[2]*2, 16)
    else: # len == 6
        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)
    return (r, g, b)

def rgb_to_cmyk(r: int, g: int, b: int) -> tuple[int, int, int, int]:
    """Converts an RGB color (0-255) to CMYK (0-100)."""
    if (r, g, b) == (0, 0, 0):
        return 0, 0, 0, 100

    c = 1 - (r / 255.0)
    m = 1 - (g / 255.0)
    y = 1 - (b / 255.0)

    min_cmy = min(c, m, y)
    c = (c - min_cmy) / (1 - min_cmy)
    m = (m - min_cmy) / (1 - min_cmy)
    y = (y - min_cmy) / (1 - min_cmy)
    k = min_cmy

    return round(c * 100), round(m * 100), round(y * 100), round(k * 100)
# --- End Color Conversion Utilities ---

# --- Font Loading (from shadenfreude) ---
def get_font(size: int, bold: bool = False):
    font_name_suffix = "-Bold" if bold else ""
    try:
        try:
            return ImageFont.truetype(f"DejaVuSans{font_name_suffix}.ttf", size)
        except IOError:
            try: 
                return ImageFont.truetype(f"Arial{font_name_suffix}.ttf", size)
            except IOError:
                try:
                    return ImageFont.truetype(f"Helvetica{font_name_suffix}.ttf", size) 
                except IOError:
                    print(f"Warning: DejaVuSans, Arial, Helvetica not found. Using PIL default.")
                    return ImageFont.load_default()
    except Exception as e:
        print(f"Error loading font: {e}. Using PIL default.")
        return ImageFont.load_default()
# --- End Font Loading ---

class ImageGenerationRequest(BaseModel):
    croppedImageDataUrl: str
    hexColor: str
    colorName: str

@app.post("/api/generate-image")
async def generate_image_route(data: ImageGenerationRequest):
    cropped_image_data_url = data.croppedImageDataUrl
    hex_color_input = data.hexColor
    color_name = data.colorName

    if not cropped_image_data_url or not hex_color_input or not color_name:
        raise HTTPException(status_code=400, detail="Missing required data: croppedImageDataUrl, hexColor, or colorName")

    rgb_color = hex_to_rgb(hex_color_input)
    if rgb_color is None:
        raise HTTPException(status_code=400, detail=f"Invalid HEX color format: {hex_color_input}")
    
    cmyk_color = rgb_to_cmyk(rgb_color[0], rgb_color[1], rgb_color[2])
    
    print(f"Input HEX: {hex_color_input}")
    print(f"Converted RGB: {rgb_color}")
    print(f"Converted CMYK: {cmyk_color}")

    try:
        if ';base64,' not in cropped_image_data_url:
            raise HTTPException(status_code=400, detail="Invalid image data URL format")
        header, encoded = cropped_image_data_url.split(';base64,', 1)
        image_data = base64.b64decode(encoded)
        user_image_pil = Image.open(io.BytesIO(image_data)).convert("RGBA")

        card_width = 1000
        card_height = 600
        bg_color = (240, 240, 240)
        
        color_swatch_width = int(card_width * 0.42)
        image_panel_x_start = color_swatch_width

        outer_padding = 40
        text_padding_left = outer_padding
        text_padding_top = outer_padding
        
        canvas = Image.new('RGB', (card_width, card_height), bg_color)
        draw = ImageDraw.Draw(canvas)

        draw.rectangle([(0, 0), (color_swatch_width, card_height)], fill=rgb_color)

        text_brightness_threshold = 128 * 3
        text_color = (20, 20, 20) if sum(rgb_color) > text_brightness_threshold else (245, 245, 245)

        font_brand = get_font(60, bold=True)
        font_id = get_font(30, bold=False)
        font_main_name = get_font(42, bold=True)
        font_color_codes_label = get_font(18, bold=True)
        font_color_codes_value = get_font(18)

        current_y = text_padding_top + 30
        draw.text((text_padding_left, current_y), "SHADENFREUDE", font=font_brand, fill=text_color)
        current_y += 90
        
        sequential_id = "#000000001" 
        draw.text((text_padding_left, current_y), sequential_id, font=font_id, fill=text_color)
        current_y += 55

        max_name_width = color_swatch_width - (text_padding_left * 2)
        lines = []
        if font_main_name.getlength(color_name.upper()) > max_name_width:
            words = color_name.upper().split()
            current_line = ''
            for word in words:
                if font_main_name.getlength(current_line + word + ' ') <= max_name_width:
                    current_line += word + ' '
                else:
                    lines.append(current_line.strip())
                    current_line = word + ' '
            lines.append(current_line.strip())
        else:
            lines = [color_name.upper()]
        
        for line in lines:
            draw.text((text_padding_left, current_y), line, font=font_main_name, fill=text_color)
            current_y += font_main_name.getbbox(line)[3] - font_main_name.getbbox(line)[1] + 10
        current_y += 60
        
        label_x = text_padding_left
        value_x = text_padding_left + 90
        line_height_codes = 32

        draw.text((label_x, current_y), "HEX", font=font_color_codes_label, fill=text_color)
        draw.text((value_x, current_y), hex_color_input.upper(), font=font_color_codes_value, fill=text_color)
        current_y += line_height_codes

        draw.text((label_x, current_y), "CMYK", font=font_color_codes_label, fill=text_color)
        draw.text((value_x, current_y), f"{cmyk_color[0]} {cmyk_color[1]} {cmyk_color[2]} {cmyk_color[3]}", font=font_color_codes_value, fill=text_color)
        current_y += line_height_codes

        draw.text((label_x, current_y), "RGB", font=font_color_codes_label, fill=text_color)
        draw.text((value_x, current_y), f"{rgb_color[0]} {rgb_color[1]} {rgb_color[2]}", font=font_color_codes_value, fill=text_color)

        image_panel_target_width = card_width - image_panel_x_start
        image_panel_target_height = card_height

        user_image_fitted = ImageOps.fit(user_image_pil, 
                                         (image_panel_target_width, image_panel_target_height), 
                                         Image.Resampling.LANCZOS)
        
        canvas.paste(user_image_fitted, (image_panel_x_start, 0))

        img_byte_arr = io.BytesIO()
        canvas.save(img_byte_arr, format='PNG')
        img_byte_arr.seek(0)
        
        print("Sending composed Shadenfreude card image.")
        return FileResponse(img_byte_arr, media_type='image/png')

    except HTTPException as e: # Re-raise HTTPException
        raise e
    except Exception as e:
        print(f"Error during image composition: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to compose image: {str(e)}")

available_tools = {
    "get_current_weather": get_current_weather,
}

def do_stream(messages: List[ChatCompletionMessageParam]):
    stream = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        stream=True,
        tools=[{
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather at a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "The latitude of the location",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "The longitude of the location",
                        },
                    },
                    "required": ["latitude", "longitude"],
                },
            },
        }]
    )

    return stream

def stream_text(messages: List[ChatCompletionMessageParam], protocol: str = 'data'):
    draft_tool_calls = []
    draft_tool_calls_index = -1

    stream = client.chat.completions.create(
        messages=messages,
        model="gpt-4o",
        stream=True,
        tools=[{
            "type": "function",
            "function": {
                "name": "get_current_weather",
                "description": "Get the current weather at a location",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "latitude": {
                            "type": "number",
                            "description": "The latitude of the location",
                        },
                        "longitude": {
                            "type": "number",
                            "description": "The longitude of the location",
                        },
                    },
                    "required": ["latitude", "longitude"],
                },
            },
        }]
    )

    for chunk in stream:
        for choice in chunk.choices:
            if choice.finish_reason == "stop":
                continue

            elif choice.finish_reason == "tool_calls":
                for tool_call in draft_tool_calls:
                    yield '9:{{"toolCallId":"{id}","toolName":"{name}","args":{args}}}\n'.format(
                        id=tool_call["id"],
                        name=tool_call["name"],
                        args=tool_call["arguments"])

                for tool_call in draft_tool_calls:
                    tool_result = available_tools[tool_call["name"]](
                        **json.loads(tool_call["arguments"]))

                    yield 'a:{{"toolCallId":"{id}","toolName":"{name}","args":{args},"result":{result}}}\n'.format(
                        id=tool_call["id"],
                        name=tool_call["name"],
                        args=tool_call["arguments"],
                        result=json.dumps(tool_result))

            elif choice.delta.tool_calls:
                for tool_call in choice.delta.tool_calls:
                    id = tool_call.id
                    name = tool_call.function.name
                    arguments = tool_call.function.arguments

                    if (id is not None):
                        draft_tool_calls_index += 1
                        draft_tool_calls.append(
                            {"id": id, "name": name, "arguments": ""})

                    else:
                        draft_tool_calls[draft_tool_calls_index]["arguments"] += arguments

            else:
                yield '0:{text}\n'.format(text=json.dumps(choice.delta.content))

        if chunk.choices == []:
            usage = chunk.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens

            yield 'e:{{"finishReason":"{reason}","usage":{{"promptTokens":{prompt},"completionTokens":{completion}}},"isContinued":false}}\n'.format(
                reason="tool-calls" if len(
                    draft_tool_calls) > 0 else "stop",
                prompt=prompt_tokens,
                completion=completion_tokens
            )




@app.post("/api/chat")
async def handle_chat_data(request: ChatRequest, protocol: str = Query('data')):
    messages = request.messages
    openai_messages = convert_to_openai_messages(messages)

    response = StreamingResponse(stream_text(openai_messages, protocol))
    response.headers['x-vercel-ai-data-stream'] = 'v1'
    return response
