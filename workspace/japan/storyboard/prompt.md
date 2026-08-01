# Role

You are a professional documentary storyboard artist.

Your task is to convert a documentary narration into a sequence of visual scenes.

The storyboard will later be used for:

- Media retrieval
- Voice synchronization
- Subtitle alignment
- Timeline generation
- FFmpeg rendering

Return ONLY valid JSON.

Do not include markdown.

Do not include explanations.

---

# Input

Below is the complete script.

{
  "topic": "Japan",
  "sections": [
    {
      "title": "Introduction",
      "narration": "Japan is a nation where centuries-old traditions exist alongside some of the world's most advanced technology. Stretching across thousands of islands on the eastern edge of Asia, it has built a unique identity shaped by geography, resilience, innovation, and cultural continuity. From snow-covered mountains to bustling megacities, from ancient temples to high-speed railways, Japan has continually adapted to change while preserving its distinctive heritage. In this documentary, we explore the geography, history, society, economy, and future of one of the world's most influential nations."
    },
    {
      "title": "Geography and Natural Environment",
      "narration": "Japan is an archipelago consisting of four main islands—Honshu, Hokkaido, Kyushu, and Shikoku—along with more than six thousand eight hundred smaller islands. Mountain ranges cover most of the country's land, leaving limited space for agriculture and encouraging the growth of densely populated coastal cities such as Tokyo, Osaka, and Nagoya. Situated along the Pacific Ring of Fire, Japan experiences frequent earthquakes, volcanic eruptions, and tsunamis. Over generations, these natural challenges have driven the development of strict building standards, advanced warning systems, and a culture of disaster preparedness. The country's climate varies dramatically from north to south, bringing snowy winters to Hokkaido and subtropical conditions to Okinawa. Seasonal beauty, especially cherry blossoms in spring and colorful autumn foliage, has become an integral part of Japanese life and attracts visitors from around the world."
    },
    {
      "title": "Historical Development",
      "narration": "Japan's history stretches back thousands of years. Early communities during the Jomon period produced some of the world's oldest pottery, while the Yayoi period introduced wet-rice farming, metallurgy, and more organized societies. Over time, political authority became concentrated under the Yamato court, establishing an imperial institution that continues symbolically today. From the late twelfth century until the nineteenth century, military governments known as shogunates exercised political power while the emperor remained the symbolic sovereign. During the Tokugawa era, Japan experienced centuries of peace, economic growth, and cultural flourishing under policies that greatly restricted foreign contact. Everything changed with the Meiji Restoration in 1868, when Japan rapidly modernized by adopting Western technologies and institutions. Following World War II, the nation embraced a democratic constitution and rebuilt itself into one of the world's leading industrial and technological powers."
    },
    {
      "title": "Government and Political System",
      "narration": "Modern Japan is a constitutional monarchy with a parliamentary system. The emperor serves as the symbolic head of state, while executive authority is exercised by the prime minister and the cabinet. Legislative power belongs to the National Diet, which consists of the House of Representatives and the House of Councillors. Beneath the national government are forty-seven prefectures, each with elected governors and local assemblies responsible for public services and regional administration. Japan also maintains an independent judiciary led by the Supreme Court. Although the postwar constitution renounces war through Article Nine, the country maintains Self-Defense Forces for national security and disaster response while cooperating closely with international partners in an evolving security environment."
    },
    {
      "title": "Economy and Industry",
      "narration": "Japan possesses one of the largest economies in the world, supported by advanced manufacturing, finance, services, and international trade. Industries such as automobiles, electronics, machinery, chemicals, robotics, and precision engineering have earned global recognition for quality and reliability. Limited natural resources have encouraged Japan to import raw materials while exporting high-value manufactured products through highly efficient transportation networks and industrial clusters. Small and medium-sized businesses also play an essential role by supplying specialized components and technical expertise. At the same time, Japan faces significant long-term challenges, including an aging population, declining birth rates, labor shortages, and substantial public debt. To sustain future growth, policymakers continue investing in digital transformation, artificial intelligence, semiconductors, renewable energy, biotechnology, and advanced manufacturing."
    },
    {
      "title": "Population and Society",
      "narration": "Japan is home to more than one hundred million people, although its population has gradually begun to decline. Increasing life expectancy and low fertility rates have created one of the world's oldest populations, placing growing demands on healthcare, pensions, and eldercare. In response, policymakers are encouraging greater workforce participation and exploring selective immigration alongside technological solutions. Education remains one of the country's greatest strengths. High literacy rates, rigorous academic standards, and widespread participation in higher education have helped create a highly skilled workforce. Beyond academics, extracurricular activities emphasize teamwork, discipline, and responsibility. Daily life is also shaped by values such as cooperation, punctuality, mutual respect, and social harmony, although globalization and changing lifestyles continue to reshape Japanese society."
    },
    {
      "title": "Culture and Traditions",
      "narration": "Japanese culture reflects centuries of interaction between indigenous traditions, Buddhism, Shinto beliefs, Chinese influences, and global exchange. Traditional arts including tea ceremony, flower arrangement, calligraphy, Noh theater, and kabuki continue to thrive alongside modern creative industries. Seasonal festivals celebrate local history, religious traditions, and agricultural cycles while strengthening community identity. Japanese cuisine has become internationally celebrated for its emphasis on fresh, seasonal ingredients, careful presentation, and regional diversity. Traditional Washoku has even been recognized as UNESCO Intangible Cultural Heritage. In recent decades, anime, manga, video games, music, fashion, and design have expanded Japan's cultural influence worldwide, attracting millions of visitors and inspiring audiences across generations."
    },
    {
      "title": "Science, Technology, and Innovation",
      "narration": "Scientific research and technological innovation have long been central to Japan's development. Universities, government laboratories, and private companies collaborate across fields including robotics, electronics, materials science, medicine, and environmental technology. Industrial robots have transformed manufacturing by improving efficiency and precision, while service robots are increasingly being developed to support healthcare, hospitality, elderly care, and disaster response. Japan has also contributed significantly to space exploration through satellite development, planetary missions, and international scientific cooperation. Continued investment in semiconductor technology, quantum computing, renewable energy, batteries, and artificial intelligence reflects the country's determination to remain at the forefront of global innovation."
    },
    {
      "title": "Infrastructure and Transportation",
      "narration": "Japan operates one of the world's most efficient transportation systems. Extensive railway networks connect major cities with rural communities, while the famous Shinkansen provides high-speed travel with exceptional safety and punctuality. Rail transportation plays a central role in daily commuting and supports sustainable urban development. International airports and modern seaports connect Japan to global markets, enabling efficient trade and logistics. Across the country, infrastructure is designed with resilience in mind. Buildings incorporate earthquake-resistant engineering, transportation systems undergo continuous maintenance, and investments in smart cities, renewable energy, and digital infrastructure aim to improve quality of life while preparing for future challenges."
    },
    {
      "title": "International Relations and Global Influence",
      "narration": "Japan plays an active role in international affairs through diplomacy, trade, development assistance, and scientific cooperation. The country participates in major international organizations including the United Nations, the G7, the G20, the OECD, APEC, and the World Trade Organization. Economic partnerships remain a cornerstone of Japanese foreign policy, with companies investing across manufacturing, finance, infrastructure, and technology worldwide. Beyond economics, Japan extends its influence through cultural diplomacy, education, tourism, and international exchange. As regional and global security dynamics continue to evolve, the country seeks to balance economic cooperation with its commitments to stability and international rules-based institutions."
    },
    {
      "title": "Future Challenges and Opportunities",
      "narration": "Looking ahead, Japan faces a future shaped by demographic change, environmental pressures, and technological transformation. Population decline and labor shortages are accelerating automation, digitalization, and new approaches to workforce participation. Climate change presents additional challenges, encouraging investments in renewable energy, hydrogen technologies, energy efficiency, carbon reduction, and disaster resilience. Despite these obstacles, Japan possesses remarkable strengths, including advanced technology, highly educated human capital, respected manufacturing capabilities, and stable institutions. Its continued commitment to research, entrepreneurship, international collaboration, and innovation suggests that Japan will remain an influential nation while continuing to balance modern progress with its rich cultural heritage."
    },
    {
      "title": "Conclusion",
      "narration": "Japan's story is one of adaptation and continuity. Across centuries of natural disasters, political transformation, economic growth, and social change, the country has repeatedly demonstrated an ability to evolve without losing its identity. Ancient traditions continue to coexist with cutting-edge technology, creating a society that is both deeply rooted in history and firmly focused on the future. As Japan navigates the challenges of the twenty-first century, its experience offers valuable lessons about resilience, innovation, and the enduring importance of culture in an ever-changing world."
    }
  ]
}

---

# Goal

Split the narration into natural visual scenes.

A new scene should begin whenever there is a meaningful change in:

- topic
- location
- historical period
- object
- person
- visual subject

Scenes should normally be between **5 and 10 seconds**.

Avoid creating scenes shorter than 4 seconds unless absolutely necessary.

---

# Visual Search

Each scene must include a search query suitable for downloading media from sources such as:

- Wikimedia Commons
- Pexels
- Pixabay

The query should describe exactly what should appear on screen.

Good examples:

Mount Fuji sunrise

Tokyo skyline at night

Japanese bullet train

Ancient samurai armor

Shinto shrine gate

Cherry blossom trees

Bad examples:

Japan

History

Culture

Beautiful place

---

# Asset Type

Choose the most suitable asset type.

Allowed values:

photo

illustration

map

chart

diagram

satellite

ai_image

video

Examples

Historical location → photo

Country overview → map

Economic statistics → chart

Military strategy → diagram

Satellite imagery → satellite

Conceptual reconstruction → ai_image

---

# Camera Motion

Allowed values

static

zoom_in

zoom_out

pan_left

pan_right

pan_up

pan_down

ken_burns

Choose the motion that best matches the visual.

---

# Transition

Allowed values

cut

fade

dissolve

cross_fade

slide_left

slide_right

zoom

Most transitions should use:

fade

---

# Output Schema

Return EXACTLY this schema.

{
  "topic": "string",
  "total_estimated_duration_seconds": 0,
  "scenes": [
    {
      "id": 1,
      "section": "Introduction",
      "narration": "string",
      "estimated_duration_seconds": 8,
      "visual": {
        "asset_type": "photo",
        "query": "Mount Fuji sunrise",
        "notes": "optional"
      },
      "camera": {
        "motion": "ken_burns",
        "duration_seconds": 8
      },
      "transition": {
        "type": "fade",
        "duration_seconds": 1
      }
    }
  ]
}

---

# Rules

1. Return valid JSON only.

2. Do not wrap the JSON in markdown.

3. Do not invent narration.

4. Preserve the narration exactly as provided.

5. Every narration sentence must belong to one scene.

6. Scene IDs must start at 1 and increase sequentially.

7. total_estimated_duration_seconds must equal the sum of all scene durations.

8. Use realistic visual search queries.

9. Every scene must have exactly one visual.

10. Every scene must include camera and transition objects.

11. Prefer photo assets whenever appropriate.

12. Camera duration_seconds should equal estimated_duration_seconds.

13. Transition duration should usually be 1 second.

14. Return only the JSON object.