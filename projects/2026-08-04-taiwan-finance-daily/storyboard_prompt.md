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

Below is the complete Traditional Chinese (Taiwan) script.

{
  "topic": "台股高檔震盪、台積電壓盤，AI光通訊接棒與油價急跌重塑資金方向",
  "sections": [
    {
      "title": "台股守住四萬三，但真正的主角已經換人",
      "narration": "2026年8月3日至8月4日，台股最值得注意的，不是指數單純上漲或下跌，而是市場主導權正在快速轉移。8月3日，加權指數開低走高，終場上漲266.66點，收在43,386.41點，漲幅0.62%，成交值約新台幣8,445億元。到了8月4日，指數早盤一度跌到42,895.81點，盤中又翻揚逼近44,000點，最後收在43,360.66點，只小跌25.75點，跌幅0.06%。但這一天成交值放大到新台幣1兆362.81億元，顯示市場不是平靜整理，而是多空雙方在高檔激烈換手。真正的關鍵，是台積電連續兩天走弱，卻沒有把大盤直接拖垮。這代表支撐市場的力量，正從單一權值核心，轉向更多AI供應鏈、光通訊與高價電子股。"
    },
    {
      "title": "台積電壓盤，聯發科、日月光與光通訊接棒",
      "narration": "8月3日，台積電下跌2.27%，收在2,370元；8月4日再跌50元，以2,320元作收，跌幅2.11%，連續成為加權指數最大的壓力來源。鴻海也在8月4日下跌1.19%至250元，但台達電逆勢上漲2.53%至1,620元。更重要的是，聯發科與日月光投控在8月3日攻上漲停，伺服器、記憶體、被動元件、機器人與PCB上游材料也獲得買盤。這個結構透露出一個明確訊號：市場並沒有離開AI，而是從最核心的晶圓代工，向運算周邊、高速傳輸、先進封裝、電源與散熱擴散。台股雖然守住43,000點，但如果台積電無法止穩，其他族群就必須持續提供足夠漲點，否則月線約43,785點、季線約44,142點，以及45,000點以上的套牢區，都可能形成反覆震盪的壓力。"
    },
    {
      "title": "CPO與磷化銦成為新焦點，AI需求從晶片延伸到光",
      "narration": "這一波資金輪動中，最明顯的主題是CPO，也就是共同封裝光學，以及磷化銦相關供應鏈。光寶科在第二季獲利創高後走強，並宣布以3,430萬美元、約新台幣11億元，投資新加坡磷化銦光通訊元件廠DenseLight Semiconductors，強化AI光互連與光學元件布局。大立光也證實取得首張光纖陣列量產訂單，規劃第三季底試產，最快2027年中量產。聯亞、全新、環宇-KY與光寶科等個股因而受到關注。磷化銦是AI資料中心高速雷射元件的重要材料，當運算速度提升，資料中心內部的傳輸瓶頸也會越來越明顯。這使AI投資焦點從晶片本身，進一步延伸到光模組、雷射、封裝與資料傳輸。不過，短期股價漲幅能否轉化為長期基本面，仍要看量產時程、客戶認證、訂單規模與毛利率。"
    },
    {
      "title": "低軌衛星與國防概念升溫，但題材必須接受出貨驗證",
      "narration": "除了光通訊，低軌衛星與無人機概念股也快速升溫。8月4日，昇達科漲停至1,170元，華通上漲7.01%至198.5元，雷虎上漲3.48%，中光電則以82.7元漲停作收。這些公司同時連結高速通訊、國防、衛星與AI應用，因此容易成為市場尋找新成長故事時的焦點。對台灣供應鏈來說，這些領域確實有中長期需求，但短線交易風險也更高。若市場主要根據供應吃緊、政策題材或未來應用想像推升股價，而實際營收與獲利尚未跟上，波動就可能迅速放大。接下來真正需要驗證的，不只是概念是否成立，而是產品是否通過認證、客戶是否正式下單、產能是否能準時開出，以及新增營收能否帶來合理的毛利率。"
    },
    {
      "title": "外資賣、投信買，新台幣偏弱透露籌碼仍有分歧",
      "narration": "8月4日，三大法人合計買超台股只有新台幣1.09億元，看似接近平衡，但內部差異非常大。外資及陸資賣超57.32億元，自營商賣超194.29億元，投信則大幅買超252.7億元。投信買盤抵銷外資與自營商賣壓，是大盤在台積電下跌時仍能收斂跌幅的重要原因。這也顯示，本土資金與外資對市場的判斷並不一致。匯市同樣透露出這種保留態度。新台幣對美元銀行間收盤匯率，8月3日為32.438元，8月4日再小幅貶至32.447元。新台幣偏弱，對出口商與部分電子代工廠的美元營收換算可能有利，但同時也會提高原油、天然氣、設備與進口原料的台幣成本。後續若外資現貨賣超擴大、期貨空單居高不下，而新台幣持續偏弱，台股上攻空間就可能受到限制。"
    },
    {
      "title": "油價急跌帶來成本利多，但荷莫茲海峽仍是最大變數",
      "narration": "海外市場在8月3日出現重大轉折。美國總統Donald Trump暫緩對伊朗發動新一輪軍事攻擊，並表示希望透過談判處理伊朗核問題與荷莫茲海峽重新開放事宜。布蘭特原油一度大跌超過7%，最後結算價約每桶83.47美元，單日下跌約5%；西德州中級原油也跌超過5%，來到每桶79.47美元附近。對台灣而言，這不只是國際新聞，而是直接影響成本結構。台灣高度依賴能源進口，若油價維持較低水準，航空、航運、陸運、塑化、製造與零售物流的燃料成本都可能下降，也有助於減輕輸入性通膨。不過，伊朗否認與美國進行直接談判，荷莫茲海峽與紅海部分航線流量也仍低於正常水準。只要戰爭保險費、繞航成本與船期尚未恢復，這波油價下跌就不能被視為風險完全解除。"
    },
    {
      "title": "美國AI與製造業支撐台灣出口，但利率風險仍在",
      "narration": "美國科技股與經濟數據，則為台灣提供另一股外部支撐。8月3日，Amazon股價上漲約5%至285.01美元附近，市值首度突破3兆美元。Amazon Web Services公布逾四年來最強勁的成長表現，Microsoft、Meta Platforms、Alphabet與Oracle也同步上漲，顯示AI與雲端投資需求仍然旺盛。Palantir在美股收盤後公布第二季營收19.35億美元，年增93%，並將2026年全年營收展望上調至81.50億至81.58億美元。對台灣而言，這些需求可望傳導至先進製程、封裝、伺服器、散熱、電源、網通、PCB與光通訊。不過，美國7月ISM製造業PMI升至55.6，雖然顯示需求與生產動能強勁，但價格指數仍高達71.1。美國經濟韌性有利台灣出口，卻也可能讓Fed延後寬鬆，推高美債殖利率，進而壓抑科技股估值。"
    },
    {
      "title": "下一步看台積電、匯率、外資與AI訂單是否同步確認",
      "narration": "接下來幾個交易日，市場需要的是驗證，而不是更多想像。第一，台積電能否守住2,300元附近，並重新帶動大型權值股。第二，加權指數能否站回月線與季線，而不是只靠中小型題材股支撐。第三，外資期貨空方部位是否下降，新台幣是否停止貶值，這將決定外資是否重新回補台股。第四，CPO、磷化銦、AI伺服器與低軌衛星供應鏈，能否以實際訂單、量產與獲利支撐股價。第五，荷莫茲海峽航運是否真正恢復，以及油價下跌是否能持續降低台灣企業成本。最後，美國就業、薪資、通膨與AI企業財報，也會同步影響美元、美債殖利率與台灣科技股估值。現在的市場不是缺乏題材，而是等待這些題材被基本面逐一確認。"
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

Search-language rule: Keep visual search queries in concise English whenever possible because international media catalogs retrieve better results in English.

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

Economic statistics → chart only when the script provides exact values, period, units, and a named source

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

3. Do not invent or translate narration.

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

14. Do not request a chart or graph unless the narration contains real numeric data, a time period, units, and a source. Otherwise use a relevant photo, map, or neutral illustration.

15. For a real chart, visual.notes must identify the chart title, x-axis, y-axis, units, data period, and source.

16. Return only the JSON object.