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
  "topic": "AI與半導體高估值遭遇長債、油價雙重壓力：費半重挫5.6%，台股面臨8月19日月結算與科技股重新定價",
  "sections": [
    {
      "title": "今日焦點｜AI高估值同時遭遇高利率與高油價",
      "narration": "8月18日全球市場最重要的訊號，來自美國半導體股的急跌。費城半導體指數SOX重挫約5.6%，30檔成分股全面下跌，Micron跌7%、Nvidia跌2.3%、Broadcom跌3.2%，Coherent與Credo Technology等高速傳輸相關股票跌幅甚至超過12%。但同一天S&P 500只下跌0.7%，Dow Jones更只跌0.2%。這個差距很重要，因為它顯示市場不是在全面拋售所有美國企業，而是集中調節先前漲幅較大、估值較高的AI、記憶體、光通訊與晶片資產。換句話說，現在市場開始重新問一個問題：AI需求確實很強，但目前股價反映的成長，是否已經跑得比實際獲利更快？第二股壓力來自債券。美國10年期公債殖利率升到約4.74%，30年期一度來到5.234%，接近2007年以來高檔。當無風險利率上升，企業融資成本提高，股票未來現金流的折現率也會上升。對AI產業尤其重要，因為大型資料中心需要GPU、網路、電力與散熱等大量前期資本支出，利率越高，市場要求的投資報酬也越高。第三股壓力來自能源。布蘭特原油升到每桶91.02美元附近，中東與荷莫茲海峽風險仍未解除。油價上升可能增加企業成本，也可能讓通膨下降速度變慢，進一步限制Fed寬鬆空間。對台灣而言，這三股力量最後會匯集到同一條傳導鏈：油價與長端利率提高成本與折現率，而台積電、記憶體、PCB、CPO與AI伺服器供應鏈，正位在這場AI重新定價的核心。"
    },
    {
      "title": "美股盤勢｜Nasdaq跌1.3%，費半跌5.6%，真正的賣壓集中在科技股",
      "narration": "接著看8月18日美股四個主要錨點。S&P 500下跌53.30點，跌幅0.7%，收在7,691.76點，連續第三個交易日從歷史高點回落。Dow Jones Industrial Average下跌116.38點，跌幅0.2%，收53,343.40點。Nasdaq Composite下跌355.20點，跌幅1.3%，收26,289.71點。真正劇烈的是費城半導體指數SOX，單日重挫約5.6%。Dow跌幅遠小於Nasdaq與SOX，再次說明這次不是所有產業同步惡化，而是科技與AI資產承受更強的估值壓力。半導體內部的分化更明顯。Micron跌約7%，Sandisk約跌9%，AMD跌4.3%，Broadcom跌3.2%，Coherent與Credo等高速網路與光通訊相關股票跌幅超過12%。這些公司先前都是AI資料中心、記憶體與高速傳輸需求的重要受惠者，因此當市場開始擔心估值過高、投資回收時間拉長時，高波動、前期漲幅較大的股票通常最先被調節。不過，這裡需要區分『基本面反轉』與『估值壓縮』。目前沒有可靠證據顯示主要雲端業者全面取消AI資料中心資本支出，所以SOX單日重挫不能直接等同AI需求崩潰。接下來如果美債殖利率回落，而AI訂單、營收與資本支出仍然強勁，這次修正比較接近估值調整；如果殖利率持續上升，同時企業開始下修AI投資，才會對台灣供應鏈形成更深層的基本面壓力。"
    },
    {
      "title": "全球股市｜美國科技股壓力傳到日本，中國AI也面臨獲利驗證",
      "narration": "美國科技股的修正，很快傳導到亞洲。8月19日東京早盤，日經225一度下跌2.7%至65,604.25點。Renesas Electronics與Fujikura一度各跌約7.2%，Sumitomo Electric Industries跌約6.7%。這些公司分別涉及半導體、電子零組件與高速資料傳輸，因此日本市場的反應說明，這次AI估值修正已經不只是華爾街內部的短期交易，而是開始影響亞洲科技供應鏈。日本同時還面臨自己的利率壓力。10年期日本公債殖利率8月18日突破2.95%，來到1996年以來高檔；8月19日東京早盤USD/JPY約159.46。對台灣而言，日本具有很高的參考價值，因為台日市場都高度集中在半導體、電子零組件與AI基礎建設。如果日本科技股在本國長端利率上升的環境下持續承壓，代表亞洲成長股的估值壓力可能比單純美股回檔更廣。中國則呈現另一種AI考驗。Baidu第二季營收年減4.2%至人民幣313.25億元，淨利大減68%至23.2億元。AI相關收入雖然年增25%，卻仍不足以抵銷核心廣告業務轉弱。這提供一個很重要的訊號：AI業務成長，不一定能立即轉化成整家公司更好的獲利。市場正在從『有沒有AI』進一步追問『AI最後能不能產生足夠現金流』。"
    },
    {
      "title": "台股焦點｜費半急跌碰上月結算，台積電成為關鍵觀察點",
      "narration": "回到台灣，8月19日面對的外部環境明顯轉弱。前一晚Nasdaq跌1.3%、SOX重挫約5.6%，Nvidia、Micron、Broadcom與多檔AI高速傳輸股票同步下跌，日本科技股早盤也明顯走弱。這使台積電、記憶體、CPO、PCB、AI伺服器、散熱、電源與高速傳輸供應鏈，成為今天最直接的風險傳導區。由於這份報告製作時8月19日台股仍在交易，因此不能把任何盤中TAIEX或台積電價格當成正式收盤，最終收盤與三大法人買賣超仍要等交易結束後確認。今天還多了一個台灣市場特有的短線變數。臺灣期貨交易所行事曆顯示，8月19日是國內股價指數期貨、股價指數選擇權、股票期貨與股票選擇權契約的月結算最後交易日。月結算本身不代表市場一定上漲或下跌，但在海外科技股劇烈修正時，期現貨部位調整、避險與轉倉可能進一步放大盤中波動。因此今天不能只看加權指數跌多少，更要觀察台積電是否相對抗跌、電子成交比重是否下降，以及AI供應鏈究竟是全面賣壓，還是前期高基期個股的估值調整。更重要的是訂單。目前沒有證據顯示全球大型雲端業者全面削減AI資本支出，但高利率會提高資料中心的融資與資本成本。如果企業開始要求更嚴格的投資回收率，才可能逐步影響GPU、HBM、先進封裝、光通訊與伺服器採購節奏。"
    },
    {
      "title": "匯率與利率｜30年美債殖利率站上5.2%，今晚Fed會議紀錄是下一個關卡",
      "narration": "接下來看這次科技股修正背後最重要的金融變數，也就是長端利率。8月18日美國10年期公債殖利率升到約4.74%，30年期殖利率升到5.234%，接近2007年6月以來最高水準。市場擔心的不只有Fed政策，還包括通膨、政府赤字、國債供給，以及AI基礎建設本身帶來的大量融資需求。這對台灣科技股非常重要，因為高成長公司的估值高度依賴多年後的現金流。折現率越高，同樣一筆未來獲利，今天能支持的股價就越低。亞洲匯率方面，8月19日東京早盤USD/JPY約159.46，略低於前一日東京市場的159.73。日圓仍在相對弱勢區域，但日本公債殖利率快速上升，使美日利差、日圓與亞洲資金配置的關係變得更加複雜。至於新台幣，由於報告製作時台北匯市仍在交易，尚未取得可靠的8月19日正式收盤USD/TWD，所以不填入預測數字。真正要看的是，如果外資因科技股風險升高而撤出亞洲，新台幣是否同步承壓；如果匯率保持穩定，則可能代表壓力主要集中在股票估值，而不是全面資本外流。下一個催化劑在今晚。Federal Reserve預定於美東時間8月19日下午2點公布7月28日至29日FOMC會議紀錄。該次會議把政策利率維持在3.5%至3.75%，但12名有投票權官員中有3人主張升息。如果會議紀錄顯示支持進一步緊縮的官員比正式投票結果更多，美債殖利率與美元可能面臨進一步上行壓力；如果Fed內部更重視成長風險，科技股目前的折現率壓力則可能有所緩和。"
    },
    {
      "title": "商品市場｜布蘭特站上91美元，油價透過通膨與利率壓向台灣科技股",
      "narration": "商品市場今天真正需要關注的是原油。8月18日布蘭特原油升到每桶91.02美元附近，美國與伊朗目前沒有新的直接談判安排，荷莫茲海峽船舶通行仍受到限制，區域內也持續出現船舶與能源設施安全事件。這代表目前的油價不只是反映實際供需，也包含相當程度的地緣政治風險溢價。只要荷莫茲海峽無法穩定恢復通行，這部分價格就很難完全消失。對台灣來說，油價突破90美元有兩條重要傳導路徑。第一條是直接成本。航空、海運、陸運、塑化、製造、電力與物流成本都可能增加，並透過進口商品形成輸入性通膨。第二條則是金融市場。油價上升提高美國通膨維持高檔的風險，讓Fed更難快速轉向寬鬆，也讓長天期美債殖利率更難下降。結果就是台灣AI與半導體公司一方面面對較高的能源與物流成本，另一方面又面對更高的全球折現率。所以接下來不能只看油價本身，而要看上漲原因是否持續。如果荷莫茲海峽通行改善、外交談判重新啟動，能源風險溢價可能下降；反過來，如果區域衝突擴大，油價、通膨預期與長端殖利率就可能互相強化，對高本益比科技股形成更大的壓力。"
    },
    {
      "title": "產業與公司焦點｜AI故事還在，但市場開始要求真正的投資報酬",
      "narration": "回到產業本身，8月18日的賣壓集中在今年漲幅較大的AI受惠股。Micron跌7%、Nvidia跌2.3%、Broadcom跌3.2%、AMD跌4.3%、Sandisk約跌9%，Coherent與Credo等高速資料傳輸股票跌幅更超過12%。這種結構顯示市場正在優先降低高波動、高估值部位。部分分析把跌勢歸因於8月成交量較低環境下的獲利了結與程式交易，但高殖利率與AI投資回收疑慮，提供了更重要的總體背景。市場真正開始問的是，AI資本支出到底能產生多少報酬。大型資料中心需要GPU、HBM、網路晶片、光通訊、電力、散熱與建築基礎設施，這些投資對台灣供應鏈當然是龐大商機；但當30年期美債殖利率超過5.2%，企業計算資本成本時使用的門檻也提高。即使硬體訂單短期仍然成長，如果AI專案需要更長時間才能產生足夠收入，市場願意支付的估值倍數仍可能下降。Baidu的財報也可以放在同一個框架理解。第二季AI相關收入年增25%，但公司整體營收仍年減4.2%，淨利大減68%。這說明AI業務快速成長，不一定能立刻抵銷成熟業務下滑與龐大投資成本。對台灣半導體、伺服器、CPO與PCB供應鏈而言，下一階段真正重要的會是客戶資本支出、訂單能見度、量產進度、毛利率與自由現金流，而不是只要貼上AI標籤就能獲得更高估值。"
    },
    {
      "title": "今日市場結論｜接下來看費半、長債、油價與Fed四個變數",
      "narration": "最後把8月18日至19日的市場串起來。現在的核心不是AI需求突然消失，而是AI資產正在接受更嚴格的估值測試。中東風險讓布蘭特原油升到91美元附近，能源與財政疑慮又讓美國10年期殖利率升至約4.74%、30年期升至5.234%。更高的無風險利率提高AI投資與資料中心的資本成本，也降低高成長科技股未來現金流的現值，因此先前漲幅最大的半導體、記憶體與高速傳輸股票成為主要調節對象，SOX單日重挫約5.6%。對台灣觀眾而言，接下來最值得追蹤四個變數。第一，SOX以及Nvidia、Micron等AI晶片股能不能止穩，並觀察台積電與台灣AI供應鏈是否出現相同程度的估值壓縮。第二，美國10年期與30年期公債殖利率是否繼續創高；長端利率如果下降，科技股的折現率壓力才可能真正減輕。第三，布蘭特原油能不能回到90美元以下，以及荷莫茲海峽船舶通行是否改善。第四，8月19日晚間公布的Fed會議紀錄，是否顯示更多官員支持升息。這四個變數會幫助我們判斷，眼前看到的是高檔獲利了結，還是全球科技股正在進入更持久的估值調整。"
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


# Timing Policy

Do NOT spend effort making duration estimates add up exactly.

- `total_estimated_duration_seconds` may be `null`.
- Scene `estimated_duration_seconds` may be `null`.
- Camera `duration_seconds` may be `null`.
- If you provide estimates, they are approximate editorial hints only.
- The application measures the real TTS narration duration and builds the final timeline from that audio.
- Content quality and correct scene/topic boundaries are more important than estimated seconds.

---

# Output Schema

Return EXACTLY this schema.

{
  "topic": "string",
  "total_estimated_duration_seconds": null,
  "scenes": [
    {
      "id": 1,
      "section": "Introduction",
      "narration": "string",
      "estimated_duration_seconds": null,
      "visual": {
        "asset_type": "photo",
        "query": "Mount Fuji sunrise",
        "notes": "optional"
      },
      "camera": {
        "motion": "ken_burns",
        "duration_seconds": null
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

7. Duration estimates are optional advisory metadata. Missing, approximate, or mismatched duration estimates are acceptable.

8. Use realistic visual search queries.

9. Every scene must have exactly one visual.

10. Every scene must include camera and transition objects.

11. Prefer photo assets whenever appropriate.

12. Camera duration_seconds is optional. Final timing will be calculated from the rendered narration audio, not from GPT estimates.

13. Transition duration should usually be 1 second.

14. Do not request a chart or graph unless the narration contains real numeric data, a time period, units, and a source. Otherwise use a relevant photo, map, or neutral illustration.

15. For a real chart, visual.notes must identify the chart title, x-axis, y-axis, units, data period, and source.

16. Return only the JSON object.