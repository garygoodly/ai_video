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
  "topic": "台股重返4萬5但量能降溫：美債殖利率、油價與美國消費壓力對抗AI記憶體投資",
  "sections": [
    {
      "title": "今日焦點｜台股重返4萬5，但資金還沒有全面回來",
      "narration": "8月20日至21日，台股連續兩個交易日反彈，但真正值得注意的不是指數重新站上45,000點，而是量能沒有同步跟上。8月20日加權指數盤中高低差超過700點，最後上漲214.39點，收在44,933.74點；8月21日早盤一度跌到44,583點附近，之後翻紅，終場再漲290.55點，收在45,224.29點，漲幅0.65%。台積電上漲近1.5%，聯發科漲逾2%，大型權值股重新提供支撐。不過，8月21日成交值只有新台幣7,192.8億元，比前一天的7,929.62億元還低，也明顯低於8月中旬部分交易日接近或突破兆元的水準。換句話說，指數回來了，但追價資金還沒有全面回來。盤面也呈現明顯輪動，萬海漲停、陽明漲逾6%、長榮漲逾2%，南亞科與華邦電也漲超過2%；相對地，欣興、景碩與南電等ABF載板股約跌5%。海外環境則讓這場反彈更複雜。美國10年期公債殖利率重新升到4.697%，30年期約5.24%，布蘭特原油也因美伊緊張升到94美元附近。另一方面，Micron又宣布未來10年投入100億美元成立Micron Research Labs。這代表今天市場的核心矛盾非常清楚：AI與半導體的實際投資沒有停止，但高利率、高能源成本與較弱的消費環境，正在限制市場願意支付的估值。"
    },
    {
      "title": "美股盤勢｜三大指數下跌，但SOX逆勢上漲透露半導體韌性",
      "narration": "接著看美股。8月20日S&P 500下跌66.82點，跌幅0.9%，收在7,641.16點；Dow Jones Industrial Average下跌703.84點，跌幅1.3%，收52,759.21點；Nasdaq Composite下跌263.92點，跌幅1%，收26,067.17點。但和三大指數不同，費城半導體指數SOX反而逆勢上漲0.53%。這個差異對台灣很重要，因為它說明當天美股面臨的主要問題，不是新的半導體需求崩潰，而是債券、能源與消費三條總體風險同時升高。第一個壓力是長端利率。美國財政部擴大長天期公債回購後，殖利率一度下降，但8月20日10年期美債殖利率又回到4.697%，30年期約5.24%。美國政府債務突破40兆美元後，市場仍在評估財政赤字與未來公債供給，這也讓高估值科技股的折現率壓力難以真正消失。第二個壓力來自Walmart。公司公布FY2027第二季總營收年增5.9%，全球電子商務銷售成長23%，但Walmart U.S.同店銷售只成長2.6%。市場重新擔心消費成長與未來獲利能力，Walmart股價單日重挫9.2%，成為Dow的重要拖累。對台灣來說，這裡要區分兩條需求鏈。美國一般消費放慢，主要影響消費電子與零售相關出口；AI資料中心則屬於企業資本支出。SOX逆勢上漲、Walmart卻重挫，正好說明美國需求不是所有領域一起轉弱。"
    },
    {
      "title": "全球股市｜日經收跌，亞洲成長股也受到高利率與能源成本牽制",
      "narration": "從美國往亞洲看，日本提供了另一個重要訊號。8月21日日經225下跌200.43點，跌幅0.30%，收在66,016.36點；TOPIX反而上漲0.19%，收4,067.29點。兩個指數方向不同，代表日本市場也不是全面性的risk-off，也就是全面降低風險部位，而是大型成長股與其他產業之間出現分化。Walmart財報帶來的消費疑慮，也拖累迅銷等消費類股。這和台灣的關係在於，日本與台灣都有大量半導體、電子零組件、設備與AI基礎建設公司。全球長端殖利率上升，會直接提高這些成長股的估值門檻；而日本和台灣又同樣高度依賴能源進口，油價維持90美元以上，也會增加企業成本與輸入性通膨。因此日股可以作為台股的重要交叉驗證。如果美國晶片股保持穩定，但日本與台灣科技股仍持續承壓，就不能只把原因歸結為美國AI交易，而需要進一步檢查亞洲本地的利率、匯率與資金流。"
    },
    {
      "title": "台股焦點｜權值股撐盤，記憶體與航運接棒，但AI內部明顯分化",
      "narration": "回到台股內部。8月20日加權指數早盤最高來到45,160.05點，之後一度下殺到44,446.36點，最後仍上漲214.39點，收44,933.74點。台積電上漲1.06%至2,375元，鴻海收246.5元，聯發科則下跌至3,700元。當天記憶體與CPO相對強勢，南亞科上漲7.48%、華邦電上漲5.06%，多檔光通訊相關股票也走強。外資結束連續兩日賣超，轉為買超37.82億元，但整體成交值降到近一個月低檔。到了8月21日，指數早盤一度下跌超過300點，之後在台積電、聯發科等權值股回升下翻紅，最後收在45,224.29點。電子類股上漲0.37%，金融類股漲2.53%，但OTC指數反而下跌0.69%，顯示大型股與中小型股並沒有同步轉強。AI供應鏈內部也出現明顯選股，記憶體延續買氣，但欣興、景碩、南電等ABF載板股約跌5%。航運則成為另一個資金出口，萬海漲停、陽明漲逾6%、長榮漲逾2%。中東航線風險可能帶來運價與供給擾動預期，但油價上升又會提高燃料成本，所以航運並不是單純的油價受惠產業。8月21日完整三大法人買賣超在截稿時尚未由可靠來源確認，因此目前更值得觀察的是成交量能否回升，以及外資能不能延續8月20日重新買超的方向。"
    },
    {
      "title": "匯率與利率｜美元轉弱，不代表科技股的資金成本已經下降",
      "narration": "接著看匯率與利率，這裡有一個很容易被忽略的分化。美國財政部擴大債券回購之後，美元指數DXY一度跌到98.7附近，接近三個月低點，但長天期美債殖利率並沒有持續下降。8月20日10年期殖利率重新升到4.697%，30年期約5.24%。財政部第三季回購時程顯示，不同期限的流動性支持操作規模多為20億至40億美元，但相對於龐大的美國國債供給，市場仍在評估這些操作能不能持續壓低期限溢酬。這對台灣非常重要。美元走弱通常有利亞洲貨幣與資金流，但如果美債長端殖利率仍高，台灣科技股的折現率壓力並沒有真正消失。8月21日台北匯市午盤，新台幣兌美元暫收31.89元，升值3.5分；因為這是午盤資料，不能當成正式收盤價。USD/JPY則維持在159附近，日圓仍相對弱勢。對台灣電子業而言，日圓偏弱會影響日本半導體材料、設備與零組件供應商的價格競爭力，也可能改變亞洲資金配置。接下來真正重要的是，如果美元繼續轉弱，但美國10年與30年期殖利率仍然居高不下，問題更可能來自美國財政與長債供給；只有當長端殖利率也明顯下降，全球高成長科技股的估值壓力才可能真正減輕。"
    },
    {
      "title": "商品市場｜布蘭特升破94美元，中東風險形成雙重成本壓力",
      "narration": "商品市場最重要的變數重新回到原油。8月20日，美國總統Donald Trump宣布加大對伊朗的經濟施壓，並警告協助伊朗金融與關鍵基礎建設的國家可能面臨美國經濟報復。在美伊直接談判仍然停滯的背景下，市場重新提高對能源供應與荷莫茲海峽風險的定價。WTI原油一度上漲近4%，來到每桶87.51美元；布蘭特原油上漲超過3%，升到94.48美元附近，來到當月較高水準。對台灣而言，真正重要的不是能源股會不會上漲，而是油價如何傳導到整體經濟。台灣高度依賴進口能源，原油上升會增加航空、航運、陸運、塑化、製造與物流成本，也可能透過進口商品推高輸入性通膨。更麻煩的是第二層金融效果。如果能源通膨讓美國長端殖利率更難下降，台灣科技股又會面臨更高的全球折現率。也就是說，油價可能同時提高企業實際成本與股票估值成本。接下來要觀察的是荷莫茲海峽實際船舶通行、外交與制裁進展，以及布蘭特原油能不能重新回到90美元以下。"
    },
    {
      "title": "產業與公司焦點｜Micron投入100億美元，AI記憶體投資仍在擴張",
      "narration": "和市場對高估值的擔憂形成鮮明對比，半導體產業仍在投入真金白銀。Micron Technology在8月20日宣布成立Micron Research Labs，計畫未來10年投入100億美元，總部設在愛達荷州Boise。研究方向涵蓋關鍵記憶體技術、先進記憶體與運算架構、先進封裝，以及未來半導體製造。旗艦研究設施預計2027年動工，未來可容納數百名研究人員。這100億美元之外，Micron先前還承諾在美國投入超過2,500億美元於製造與研發。這項投資對台灣具有直接傳導意義。Micron表示，新研究網路將串聯美國、歐洲、日本、印度、新加坡與台灣的研究及技術據點。隨著AI工作負載增加，HBM，也就是高頻寬記憶體，已經成為GPU與AI加速器的重要瓶頸之一，也讓記憶體、先進封裝與高速互連的技術價值提高。這和8月20日至21日南亞科、華邦電等台灣記憶體股相對強勢形成呼應，但要注意，Micron宣布投資不代表所有台灣記憶體公司都會直接取得訂單。現在市場其實同時存在兩件事：AI與半導體企業仍在大規模投資，但股票市場對這些投資的報酬要求正在提高。高利率意味著Micron、雲端業者與資料中心營運商都必須證明資本支出能產生足夠回報。對台灣的記憶體、先進封裝、PCB、CPO、伺服器與散熱供應鏈而言，下一階段真正重要的仍是客戶資本支出、訂單能見度、量產速度、毛利率與自由現金流，而不是單純依靠AI題材。"
    },
    {
      "title": "今日市場結論｜接下來看量能、長債、油價與AI訂單四個變數",
      "narration": "最後把8月20日至21日的市場串起來。現在不是典型的risk-on，也不是全面risk-off。台股連續反彈並重新站上45,000點，SOX在美股下跌時仍逆勢上漲，Micron也宣布100億美元的長期AI記憶體研究投資，這些訊號都說明半導體與AI基本面目前沒有被證明反轉。但另一方面，美國長端公債殖利率重新上升、布蘭特原油突破94美元，而Walmart股價重挫又提醒市場，美國一般消費需求仍有壓力。結果就是資金願意留在市場裡，卻不願像之前一樣無差別提高所有AI股票的估值。對台灣觀眾而言，接下來可以集中追蹤四個變數。第一，TAIEX站回45,000點之後，成交值能不能從7,000多億元明顯回升，確認反彈有新的資金加入。第二，美國10年期與30年期公債殖利率能不能真正從4.7%與5.2%左右的高檔下降。第三，布蘭特原油能不能跌回90美元以下，以及荷莫茲海峽與美伊關係是否降溫。第四，Micron的記憶體投資與接下來Nvidia等AI企業財報，能不能繼續證明AI資本支出與終端需求。這四個條件，將幫助判斷台股目前的反彈究竟只是區間內的震盪修復，還是能進一步形成由基本面與資金共同支持的趨勢。"
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