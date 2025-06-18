import os
from PIL import Image, ImageDraw

# Create a simple PNG logo
def create_simple_logo_png():
    try:
        img = Image.new('RGB', (200, 80), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        
        # Draw blue border
        draw.rectangle([(0, 0), (199, 79)], outline=(0, 98, 204), width=2)
        
        # Draw "PLUS" text in blue
        for x in range(45, 48):
            for y in range(15, 35):
                draw.text((x, y), "PLUS", fill=(0, 98, 204))
        
        # Draw "Analyzer" text in dark gray
        for x in range(40, 43):
            for y in range(40, 56):
                draw.text((x, y), "Analyzer", fill=(51, 51, 51))
        
        # Chart bars (simplified)
        draw.rectangle([(15, 48), (20, 63)], fill=(220, 53, 69))
        draw.rectangle([(22, 53), (27, 63)], fill=(253, 126, 20))
        draw.rectangle([(29, 45), (34, 63)], fill=(0, 98, 204))
        
        # Save the PNG
        os.makedirs('static', exist_ok=True)
        img.save('static/logo.png')
        print("Created logo.png")
        return True
    except Exception as e:
        print(f"Error creating logo: {e}")
        return False

# Create a simple favicon (blue square with white P)
def create_simple_favicon():
    try:
        img = Image.new('RGB', (32, 32), color=(0, 98, 204))
        draw = ImageDraw.Draw(img)
        
        # Draw a white "P" (thicker by drawing multiple times)
        for x in range(8, 11):
            for y in range(6, 9):
                draw.text((x, y), "P", fill=(255, 255, 255))
        
        # Save the favicon
        img.save('static/favicon.ico')
        print("Created favicon.ico")
        return True
    except Exception as e:
        print(f"Error creating favicon: {e}")
        return False

if __name__ == '__main__':
    # Create static directory if it doesn't exist
    os.makedirs('static', exist_ok=True)
    
    # Create logo and favicon
    logo_created = create_simple_logo_png()
    favicon_created = create_simple_favicon()
    
    if logo_created and favicon_created:
        print("Assets preparation complete")
    else:
        print("Warning: Some assets could not be created")
