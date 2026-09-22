import re
from typing import List, Dict, Optional


class TagOptimizer:
    """
    Optimizes hashtags and account tags for maximum Instagram & Facebook algorithm visibility.
    Balances Broad (Viral) + Targeted Niche + Keyword-specific tags.
    """
    NICHE_TAG_BUNDLES: Dict[str, List[str]] = {
        "Science & Space": [
            "#spacefacts", "#astronomy", "#universe", "#cosmos", "#deepspace",
            "#blackhole", "#sciencefacts", "#quantum", "#astrophysics", "#spacetok",
            "#viralreels", "#explorepage", "#didyouknow", "#mindblowing"
        ],
        "Motivation & Mindset": [
            "#motivation", "#stoicism", "#mindset", "#discipline", "#successhabits",
            "#selfimprovement", "#focus", "#grind", "#dailyquotes", "#inspiration",
            "#viralreels", "#explorepage", "#reelsindia", "#fyp"
        ],
        "AI & Future Tech": [
            "#artificialintelligence", "#futuretech", "#technews", "#robotics",
            "#cyberpunk", "#techtrends", "#aitools", "#innovation", "#gadgets",
            "#viralreels", "#explorepage", "#techreels", "#trending"
        ],
        "Dark History & Mysteries": [
            "#ancienthistory", "#darkhistory", "#mysteries", "#ancientmysteries",
            "#unexplained", "#historicalfacts", "#conspiracy", "#mythology",
            "#viralreels", "#explorepage", "#didyouknow", "#historytok"
        ],
        "Psychology Facts": [
            "#psychologyfacts", "#humanbehavior", "#darkpsychology", "#bodylanguage",
            "#psychologytricks", "#mentalhealth", "#subconscious", "#brainfacts",
            "#viralreels", "#explorepage", "#factsdaily", "#fyp"
        ],
        "Business & Wealth": [
            "#businessmindset", "#moneytips", "#wealthbuilding", "#investing",
            "#entrepreneur", "#financialfreedom", "#millionairemindset", "#passiveincome",
            "#viralreels", "#explorepage", "#businessreels"
        ]
    }

    GLOBAL_VIRAL_TAGS = ["#reels", "#reelsinstagram", "#viral", "#explorepage", "#trending", "#fyp"]

    @classmethod
    def generate_tags(
        cls,
        prompt: str,
        niche: str = "General",
        custom_tags: Optional[str] = None,
        custom_mentions: Optional[str] = None,
        max_tags: int = 15
    ) -> Dict[str, Any]:
        """
        Builds an optimized hashtag list and formatted caption footer with mentions.
        """
        tags = set()

        # 1. Niche tags
        niche_tags = cls.NICHE_TAG_BUNDLES.get(niche, cls.GLOBAL_VIRAL_TAGS)
        for t in niche_tags[:8]:
            tags.add(t.lower())

        # 2. Extract keyword tags from prompt
        words = re.findall(r"\b[A-Za-z]{4,}\b", prompt.lower())
        for w in words[:4]:
            if w not in ["this", "that", "what", "with", "from", "your", "more", "have", "about"]:
                tags.add(f"#{w}")

        # 3. Add global viral boosters
        for vt in cls.GLOBAL_VIRAL_TAGS[:4]:
            tags.add(vt)

        # 4. Add user-provided custom tags
        if custom_tags:
            for ct in custom_tags.split(","):
                ct_clean = ct.strip()
                if ct_clean:
                    if not ct_clean.startswith("#"):
                        ct_clean = f"#{ct_clean}"
                    tags.add(ct_clean.lower())

        final_tag_list = list(tags)[:max_tags]

        # 5. Format mentions
        mentions_list = []
        if custom_mentions:
            for m in custom_mentions.split(","):
                m_clean = m.strip()
                if m_clean:
                    if not m_clean.startswith("@"):
                        m_clean = f"@{m_clean}"
                    mentions_list.append(m_clean)

        tag_string = " ".join(final_tag_list)
        mention_string = " ".join(mentions_list)

        return {
            "tags": final_tag_list,
            "tag_string": tag_string,
            "mentions": mentions_list,
            "mention_string": mention_string
        }

    @classmethod
    def format_optimized_caption(
        cls,
        base_caption: str,
        tags_data: Dict[str, Any],
        call_to_action: str = "Follow for daily discoveries! 🔔 Double tap if this blew your mind."
    ) -> str:
        """Assembles high-retention caption with Hook, Body, CTA, Mentions, and Tag bundle."""
        parts = [base_caption.strip()]

        if call_to_action:
            parts.append(f"\n{call_to_action}")

        if tags_data.get("mention_string"):
            parts.append(f"\nCreated with: {tags_data['mention_string']}")

        if tags_data.get("tag_string"):
            parts.append(f"\n.\n.\n{tags_data['tag_string']}")

        return "\n".join(parts)


if __name__ == "__main__":
    res = TagOptimizer.generate_tags(
        "Ancient hidden underground city with 20000 residents",
        niche="Dark History & Mysteries",
        custom_tags="#ndtechhub, #ancientsecrets",
        custom_mentions="@NDTechHub"
    )
    caption = TagOptimizer.format_optimized_caption("Did you know this shocking history?", res)
    print("Formatted Caption:\n", caption)
