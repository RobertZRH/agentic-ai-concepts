"""Mock RSS feed data for offline unit tests."""

LEFT_FEED_ENTRIES = [
    {
        "title": "Climate scientists warn of accelerating change",
        "summary": "Leading climate researchers say global temperatures are rising faster than projected.",
        "link": "https://www.cnn.com/article/climate-1",
        "published": "Wed, 07 May 2026 10:00:00 GMT",
        "source_label": "CNN",
    },
    {
        "title": "Federal Reserve holds rates amid inflation concerns",
        "summary": "The Fed kept interest rates unchanged as Jerome Powell cited persistent inflation.",
        "link": "https://www.theguardian.com/article/fed-1",
        "published": "Wed, 07 May 2026 09:30:00 GMT",
        "source_label": "The Guardian",
    },
    {
        "title": "Economy shows mixed signals as job growth slows",
        "summary": "The economy added fewer jobs than expected last month, raising questions about growth.",
        "link": "https://www.theguardian.com/article/economy-1",
        "published": "Wed, 07 May 2026 09:00:00 GMT",
        "source_label": "The Guardian",
    },
    {
        "title": "Border crossings reach record high this quarter",
        "summary": "NPR reports that immigration at the southern border has surged in recent months.",
        "link": "https://www.npr.org/article/border-1",
        "published": "Wed, 07 May 2026 08:00:00 GMT",
        "source_label": "NPR",
    },
]

RIGHT_FEED_ENTRIES = [
    {
        "title": "Fed rate hold raises questions about inflation fight",
        "summary": "Fox News analysts question whether the Federal Reserve is doing enough to fight inflation.",
        "link": "https://www.foxnews.com/article/fed-1",
        "published": "Wed, 07 May 2026 09:45:00 GMT",
        "source_label": "Fox News",
    },
    {
        "title": "Record border crossings strain local communities",
        "summary": "NY Post reports that towns near the southern border are overwhelmed by the surge in migrants.",
        "link": "https://nypost.com/article/border-1",
        "published": "Wed, 07 May 2026 08:15:00 GMT",
        "source_label": "NY Post",
    },
    {
        "title": "WSJ: Trade tariffs may dampen economic growth",
        "summary": "Wall Street Journal opinion says new tariffs risk slowing US GDP growth.",
        "link": "https://www.wsj.com/article/tariffs-1",
        "published": "Wed, 07 May 2026 07:00:00 GMT",
        "source_label": "WSJ Opinion",
    },
]

MOCK_SUMMARIES_LEFT = [
    {
        "article_id": "left-1",
        "source_label": "CNN",
        "lean": "left",
        "original_title": "Climate scientists warn of accelerating change",
        "summary_text": "Climate researchers report temperatures are rising faster than models predicted. The study highlights increased frequency of extreme weather events. Scientists call for immediate policy action.",
    },
    {
        "article_id": "left-2",
        "source_label": "The Guardian",
        "lean": "left",
        "original_title": "Federal Reserve holds rates amid inflation concerns",
        "summary_text": "The Federal Reserve kept interest rates unchanged at its May meeting. Jerome Powell cited ongoing inflation pressures as a key concern. Analysts expect rates to remain elevated through summer.",
    },
]

MOCK_SUMMARIES_RIGHT = [
    {
        "article_id": "right-1",
        "source_label": "Fox News",
        "lean": "right",
        "original_title": "Fed rate hold raises questions about inflation fight",
        "summary_text": "Fox News analysts questioned the Federal Reserve decision to hold rates steady. Jerome Powell defended the move citing data dependency. Critics argue the Fed is falling behind the curve on inflation.",
    },
    {
        "article_id": "right-2",
        "source_label": "NY Post",
        "lean": "right",
        "original_title": "Record border crossings strain local communities",
        "summary_text": "Record numbers of migrants crossed the southern border this quarter. Local officials say resources are stretched beyond capacity. The Biden administration has not commented on new measures.",
    },
]

MOCK_BIAS_SCORES = [
    {
        "article_id": "left-1",
        "source_label": "CNN",
        "lean_score": -0.5,
        "lean_label": "center-left",
        "key_claims": ["temperatures rising faster than projected", "extreme weather increasing"],
        "framing_notes": "Frames climate change as an urgent crisis requiring policy intervention.",
        "named_entities": ["EPA", "IPCC", "carbon emissions"],
    },
    {
        "article_id": "left-2",
        "source_label": "The Guardian",
        "lean_score": -0.4,
        "lean_label": "center-left",
        "key_claims": ["Fed held rates", "inflation persists", "Jerome Powell cited data"],
        "framing_notes": "Neutral reporting with slight emphasis on worker impact of high rates.",
        "named_entities": ["Federal Reserve", "Jerome Powell", "interest rates", "inflation"],
    },
    {
        "article_id": "right-1",
        "source_label": "Fox News",
        "lean_score": 0.6,
        "lean_label": "right",
        "key_claims": ["Fed held rates", "inflation fight questioned", "Jerome Powell defended decision"],
        "framing_notes": "Frames Fed inaction as a policy failure, emphasizing inflation harm to consumers.",
        "named_entities": ["Federal Reserve", "Jerome Powell", "interest rates", "inflation"],
    },
    {
        "article_id": "right-2",
        "source_label": "NY Post",
        "lean_score": 0.7,
        "lean_label": "right",
        "key_claims": ["record border crossings", "local resources strained", "no administration response"],
        "framing_notes": "Emphasizes burden on communities, frames migration as a crisis without solutions.",
        "named_entities": ["border patrol", "southern border", "migrants", "Biden administration"],
    },
]
