import random
import re
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

HOOK_TEMPLATES = [
    "Wait for the end... you won't believe what he said! 💀",
    "This scene had the entire room in silence 🔥",
    "Bro literally did not hesitate for a second 😂",
    "Nobody was ready for this reply 🍿",
    "Absolute savage timing right here ⚡",
    "The way everyone reacted in the last 5 seconds 💀",
    "Watch closely at the climax... sheer madness 🚀",
    "Can't stop laughing at this specific part 😂",
    "This moment alone broke the entire internet 🔥",
    "Peak entertainment moment from this episode 🎬"
]

CTA_TEMPLATES = [
    "Full uncut episode uploaded on Telegram: @GhostTrafficHub (Link in Bio)",
    "Watch the complete uncensored version on Telegram: @GhostTrafficHub",
    "Direct Telegram download link available in bio: @GhostTrafficHub",
    "Stream the complete full-length cut on Telegram: @GhostTrafficHub",
    "Access the master uncut stream on Telegram: @GhostTrafficHub"
]

HASHTAG_POOLS = [
    ["#indiasgotlatent", "#samayraina", "#latent", "#mcstan", "#tanmaybhat"],
    ["#comedyreels", "#standupcomedy", "#indiancomedy", "#viralreels", "#shorts"],
    ["#trendingreels", "#explorepage", "#reelsindia", "#funnyclips", "#fyp"],
    ["#highretention", "#roasting", "#darkhumor", "#reelitfeelit", "#viralvideo"],
    ["#memesdaily", "#laughing", "#epicmoments", "#reaction", "#clout"]
]

def clean_video_name(filename):
    clean = re.sub(r'\.mp4$', '', filename, flags=re.IGNORECASE)
    clean = re.sub(r'part[_-]?\d+', '', clean, flags=re.IGNORECASE)
    clean = clean.replace('_', ' ').replace('-', ' ').strip()
    return clean

def generate_ai_caption(filename, part_num, total_parts=69, custom_cta=None):
    hook = random.choice(HOOK_TEMPLATES)
    cta = custom_cta or random.choice(CTA_TEMPLATES)
    title = clean_video_name(filename)
    
    # Pick 2 random pools and sample 6-8 tags
    p1 = random.choice(HASHTAG_POOLS)
    p2 = random.choice([p for p in HASHTAG_POOLS if p != p1])
    tags = list(set(random.sample(p1, 3) + random.sample(p2, 3)))
    random.shuffle(tags)

    part_badge = f"[PART {part_num:02d} / {total_parts}]" if total_parts else f"[PART {part_num:02d}]"

    caption = (
        f"{part_badge} {hook}\n\n"
        f"Episode: {title}\n\n"
        f"👉 {cta}\n"
        f".\n.\n"
        f"{' '.join(tags)}"
    )
    return caption

if __name__ == "__main__":
    test_caption = generate_ai_caption("INDIA'S GOT LATENT S2 EP8 ft. MC Stan_part_02.mp4", 2)
    print("Sample Generated Caption:\n")
    print(test_caption)
