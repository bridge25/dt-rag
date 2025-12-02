"""
Generate 16 3D robot images for SPEC-FRONTEND-REDESIGN-001
Robot rarities: Common (4), Rare (4), Epic (4), Legendary (4)
"""

import sys
import os
from pathlib import Path

# Add skill modules to path
skill_path = Path(".claude/skills/moai-connector-nano-banana/modules")
sys.path.insert(0, str(skill_path.resolve()))

from image_generator import NanoBananaImageGenerator
import time

# Define robot prompts for each rarity tier
ROBOT_PROMPTS = {
    "common": [
        "Cute chibi-style 3D robot character, simple design, friendly smile, metallic silver body, small antenna, standing pose, cute expressive eyes, friendly and approachable, soft studio lighting, professional 3D render, dark transparent background, high quality",
        "Adorable mini 3D robot, round head with blue LED eyes, basic body design with mechanical joints, waving pose, metallic gray-blue colors, cute proportions, soft lighting, professional render quality",
        "Friendly helper 3D robot, chibi proportions with cute round features, gray-blue metallic body, happy expression with large eyes, arms at sides, standing confidently, professional 3D animation style",
        "Cute service 3D robot, small and round design, shiny silver chrome finish, gentle expressive eyes, neutral standing pose, simple mechanical details, professional studio lighting, friendly appearance",
    ],
    "rare": [
        "Cute chibi 3D robot with glowing cyan circuit lines and patterns, friendly expression, advanced metallic body design, more detailed features, cyan LED accents, happy pose, professional 3D render",
        "Adorable advanced 3D robot with cyan LED highlights running through body, chibi style with detailed features, silver-blue metallic finish, tech patterns and circuit designs, expressive eyes",
        "Friendly elite 3D robot with glowing cyan eyes and energy accents, advanced antenna design, chibi proportions, happy confident pose, metallic body with cyan glow effects",
        "Cute 3D robot with visible cyan energy core glowing inside body, chibi proportions with detailed mechanical features, metallic silver finish with cyan accents, advanced design",
    ],
    "epic": [
        "Cute chibi 3D robot with purple energy aura surrounding body, advanced detailed design, friendly happy expression, metallic body with purple glow effects, powerful but cute appearance, professional render",
        "Adorable elite 3D robot with purple glowing accents and energy effects, advanced design with more intricate details, chibi style proportions, purple LED eyes, powerful yet friendly",
        "Friendly epic 3D robot with purple circuit patterns glowing throughout body, advanced features and details, chibi proportions, happy expression, metallic purple-silver color scheme",
        "Cute advanced 3D robot with purple energy wings or aura effect, chibi proportions with elite design, metallic silver-purple color scheme, glowing effects, powerful friendly appearance",
    ],
    "legendary": [
        "Cute chibi 3D robot wearing golden crown, holographic shimmer effects, legendary aura surrounding body, friendly happy expression, advanced metallic design, sparkling details, professional render",
        "Adorable golden 3D robot with sparkling holographic effects, chibi style with majestic appearance, golden metallic finish with rainbow iridescence, cute but regal expression",
        "Friendly legendary 3D robot with gold accents and holographic glow effects, advanced premium design, chibi proportions, happy expression, shimmering golden finish",
        "Cute 3D robot with golden energy halo and sparkles, chibi proportions with regal design, golden metallic finish, legendary appearance, professional animation quality",
    ],
}

def generate_robots():
    """Generate all 16 robot images"""
    try:
        # Initialize generator
        print("Initializing Nano Banana Image Generator...")
        generator = NanoBananaImageGenerator()
        
        # Create output directory
        output_base = Path("apps/frontend/public/assets/agents")
        
        total_generated = 0
        total_failed = 0
        
        # Generate robots for each rarity
        for rarity, prompts in ROBOT_PROMPTS.items():
            print(f"\n{'='*80}")
            print(f"Generating {rarity.upper()} tier robots ({len(prompts)} images)")
            print(f"{'='*80}")
            
            output_dir = output_base / rarity
            output_dir.mkdir(parents=True, exist_ok=True)
            
            for idx, prompt in enumerate(prompts, 1):
                try:
                    filename = f"robot-{rarity}-{idx:02d}.webp"
                    filepath = output_dir / filename
                    
                    print(f"\n[{rarity.upper()} {idx}/{len(prompts)}] Generating: {filename}")
                    print(f"Prompt: {prompt[:60]}...")
                    
                    # Generate image
                    image, metadata = generator.generate(
                        prompt=prompt,
                        model="pro",
                        aspect_ratio="1:1",  # Square for robots
                        save_path=str(filepath)
                    )
                    
                    print(f"✅ Saved: {filepath}")
                    total_generated += 1
                    
                    # Rate limiting - wait between requests
                    if idx < len(prompts):
                        print("⏳ Waiting before next generation...")
                        time.sleep(3)
                    
                except Exception as e:
                    print(f"❌ Error generating {filename}: {e}")
                    total_failed += 1
                    time.sleep(2)
        
        # Summary
        print(f"\n{'='*80}")
        print("📊 Generation Summary")
        print(f"{'='*80}")
        print(f"✅ Successfully generated: {total_generated} images")
        print(f"❌ Failed: {total_failed} images")
        print(f"📁 Output directory: {output_base.resolve()}")
        print(f"{'='*80}\n")
        
        return total_generated, total_failed
        
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        return 0, len(ROBOT_PROMPTS) * 4

if __name__ == "__main__":
    os.chdir("/Volumes/d/users/tony/Desktop/projects/dt-rag")
    success, failed = generate_robots()
    sys.exit(0 if failed == 0 else 1)
