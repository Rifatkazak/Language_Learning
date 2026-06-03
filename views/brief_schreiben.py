import random
import streamlit as st

from services.ai_service import get_ai_service
from services.gamification import add_xp
from storage.user_store import persist_current_user
from core.i18n import t

# fmt: off
PROMPTS = [
    {
        "id": "geburtstag_absage",
        "formal": False,
        "subject_tr": "Arkadaşının doğum günü davetini reddetme",
        "subject_en": "Declining a friend's birthday invitation",
        "task_tr": "Arkadaşın seni doğum günü partisine davet etti. Maalesef gidemiyorsun. Ona bir e-posta yaz.",
        "task_en": "Your friend invited you to their birthday party. Unfortunately you cannot attend. Write them an email.",
        "points_tr": ["Neden gidemediğini açıkla", "Özür dile", "Başka bir buluşma öner", "Doğum günü dile"],
        "points_en": ["Explain why you can't come", "Apologize sincerely", "Suggest another time to meet", "Wish them happy birthday"],
        "hint_structure": "Betreff: Deine Einladung\n\nLiebe(r) [Name],\n\nvielen Dank für deine Einladung! Leider...\n\n[Erklärung warum]\n[Entschuldigung]\n[Vorschlag für ein anderes Treffen]\n[Glückwunsch]\n\nViele Grüße,\n[Dein Name]",
        "hint_phrases_tr": "Leider kann ich nicht kommen, weil... · Es tut mir wirklich leid, dass... · Wie wäre es, wenn wir uns am ... treffen? · Ich wünsche dir alles Gute zum Geburtstag!",
        "hint_phrases_en": "Leider kann ich nicht kommen, weil... · Es tut mir wirklich leid, dass... · Wie wäre es, wenn wir uns am ... treffen? · Ich wünsche dir alles Gute zum Geburtstag!",
        "hint_example": "Liebe Maria, vielen Dank für deine Einladung zu deiner Geburtstagsfeier! Leider kann ich leider nicht kommen, weil ich an diesem Wochenende arbeiten muss.",
    },
    {
        "id": "laerm_beschwerde",
        "formal": True,
        "subject_tr": "Komşu gürültüsü hakkında şikayet",
        "subject_en": "Complaint about neighbour noise",
        "task_tr": "Komşun çok gürültü yapıyor ve uyuyamıyorsun. Ev sahibine resmi bir e-posta yaz.",
        "task_en": "Your neighbour makes too much noise and you can't sleep. Write a formal email to your landlord.",
        "points_tr": ["Sorunu açıkla", "Ne zamandır devam ettiğini belirt", "Nasıl etkilendiğini anlat", "Çözüm talep et"],
        "points_en": ["Describe the problem", "State how long it has been going on", "Explain how you are affected", "Request a solution"],
        "hint_structure": "Betreff: Lärmproblem in der Wohnung\n\nSehr geehrte(r) Herr/Frau [Name],\n\nich schreibe Ihnen, weil...\n\n[Problembeschreibung]\n[Zeitraum]\n[Auswirkungen]\n[Bitte um Lösung]\n\nMit freundlichen Grüßen,\n[Ihr Name]",
        "hint_phrases_tr": "Ich schreibe Ihnen bezüglich... · Seit einigen Wochen... · Dadurch kann ich nicht schlafen... · Ich bitte Sie daher, ... · Ich würde mich über eine baldige Rückmeldung freuen.",
        "hint_phrases_en": "Ich schreibe Ihnen bezüglich... · Seit einigen Wochen... · Dadurch kann ich nicht schlafen... · Ich bitte Sie daher, ... · Ich würde mich über eine baldige Rückmeldung freuen.",
        "hint_example": "Sehr geehrte Frau Müller, ich schreibe Ihnen, weil ich ein Problem mit meinem Nachbarn habe. Seit drei Wochen macht er jeden Abend sehr laute Musik.",
    },
    {
        "id": "kurs_anfrage",
        "formal": True,
        "subject_tr": "Dil kursu hakkında bilgi talebi",
        "subject_en": "Inquiry about a language course",
        "task_tr": "Bir dil okulunun reklamını gördün. Kurs hakkında daha fazla bilgi almak istiyorsun. Resmi bir e-posta yaz.",
        "task_en": "You saw an advertisement for a language school. You want more information about the course. Write a formal email.",
        "points_tr": ["Kurs hakkında nasıl öğrendiğini belirt", "Kurs süresi ve saatlerini sor", "Fiyat sor", "Kayıt için ne gerektiğini sor"],
        "points_en": ["Mention how you found out about the course", "Ask about duration and schedule", "Ask about the price", "Ask what is needed to register"],
        "hint_structure": "Betreff: Anfrage zum Deutschkurs\n\nSehr geehrte Damen und Herren,\n\nich habe Ihre Anzeige gelesen und interessiere mich für...\n\n[Frage 1]\n[Frage 2]\n[Frage 3]\n[Abschluss]\n\nMit freundlichen Grüßen,\n[Ihr Name]",
        "hint_phrases_tr": "Ich habe Ihre Anzeige in ... gesehen · Ich würde gerne wissen, ob... · Wie lange dauert der Kurs? · Was kostet der Kurs? · Welche Unterlagen benötige ich für die Anmeldung?",
        "hint_phrases_en": "Ich habe Ihre Anzeige in ... gesehen · Ich würde gerne wissen, ob... · Wie lange dauert der Kurs? · Was kostet der Kurs? · Welche Unterlagen benötige ich für die Anmeldung?",
        "hint_example": "Sehr geehrte Damen und Herren, ich habe Ihre Anzeige in der Zeitung gelesen und interessiere mich sehr für Ihren Deutschkurs.",
    },
    {
        "id": "einladung_annehmen",
        "formal": False,
        "subject_tr": "Bir etkinliğe daveti kabul etme",
        "subject_en": "Accepting an invitation to an event",
        "task_tr": "Arkadaşın seni bir konsere davet etti. Memnuniyetle kabul ediyorsun. Bir e-posta yaz.",
        "task_en": "Your friend invited you to a concert. You are happy to accept. Write an email.",
        "points_tr": ["Daveti kabul ettiğini belirt", "Neden memnun olduğunu açıkla", "Bir soru sor (saat, yer vs.)", "Buluşmayı dört gözle beklediğini söyle"],
        "points_en": ["Confirm you accept the invitation", "Explain why you are excited", "Ask a question (time, place, etc.)", "Say you look forward to it"],
        "hint_structure": "Betreff: Konzerteinladung\n\nLiebe(r) [Name],\n\nvielen Dank für deine Einladung! Ich komme sehr gerne mit...\n\n[Begeisterung ausdrücken]\n[Frage stellen]\n[Freude ausdrücken]\n\nBis bald!\n[Dein Name]",
        "hint_phrases_tr": "Ich freue mich sehr, dass... · Ich komme gerne mit! · Wann und wo treffen wir uns? · Ich kann es kaum erwarten! · Das wird sicher toll!",
        "hint_phrases_en": "Ich freue mich sehr, dass... · Ich komme gerne mit! · Wann und wo treffen wir uns? · Ich kann es kaum erwarten! · Das wird sicher toll!",
        "hint_example": "Lieber Tom, vielen Dank für deine Einladung zum Konzert! Ich komme wirklich sehr gerne mit – ich liebe diese Band!",
    },
    {
        "id": "zimmer_kuendigung",
        "formal": True,
        "subject_tr": "Kiralık oda/dairenin sözleşmesini feshetme",
        "subject_en": "Cancelling a rental room/apartment contract",
        "task_tr": "Kiralık odandan taşınmak istiyorsun. Ev sahibine resmi bir fesih e-postası yaz.",
        "task_en": "You want to move out of your rented room. Write a formal cancellation email to your landlord.",
        "points_tr": ["Ayrılmak istediğini belirt", "Ayrılma tarihini yaz", "Sebep ver", "Depozito iadesi iste"],
        "points_en": ["State that you want to move out", "Give the move-out date", "Give a reason", "Request the deposit back"],
        "hint_structure": "Betreff: Kündigung meines Mietvertrags\n\nSehr geehrte(r) Herr/Frau [Name],\n\nhiermit kündige ich meinen Mietvertrag zum [Datum]...\n\n[Grund]\n[Bitte um Kaution]\n[Abschluss]\n\nMit freundlichen Grüßen,\n[Ihr Name]",
        "hint_phrases_tr": "Hiermit kündige ich... zum ... · Ich möchte aus folgendem Grund ausziehen: · Ich bitte Sie, die Kaution von ... Euro zurückzuüberweisen · Ich bedanke mich für die gute Zusammenarbeit.",
        "hint_phrases_en": "Hiermit kündige ich... zum ... · Ich möchte aus folgendem Grund ausziehen: · Ich bitte Sie, die Kaution von ... Euro zurückzuüberweisen · Ich bedanke mich für die gute Zusammenarbeit.",
        "hint_example": "Sehr geehrte Frau Schmidt, hiermit kündige ich meinen Mietvertrag fristgerecht zum 31. März, da ich in eine andere Stadt ziehe.",
    },
    {
        "id": "rat_fragen",
        "formal": False,
        "subject_tr": "Arkadaşından tavsiye isteme",
        "subject_en": "Asking a friend for advice",
        "task_tr": "Yeni bir iş teklifi aldın ama kararsızsın. Arkadaşına e-posta yaz ve tavsiye iste.",
        "task_en": "You received a new job offer but you're undecided. Write to your friend and ask for advice.",
        "points_tr": ["Durumu açıkla", "Avantajları belirt", "Dezavantajları belirt", "Tavsiyesini iste"],
        "points_en": ["Explain the situation", "Mention the advantages", "Mention the disadvantages", "Ask for their advice"],
        "hint_structure": "Betreff: Ich brauche deinen Rat!\n\nLiebe(r) [Name],\n\nich habe ein Problem und brauche deinen Rat...\n\n[Situation erklären]\n[Vorteile]\n[Nachteile]\n[Um Rat bitten]\n\nLiebe Grüße,\n[Dein Name]",
        "hint_phrases_tr": "Ich brauche dringend deinen Rat · Stell dir vor, ich habe... · Einerseits... andererseits... · Was würdest du an meiner Stelle tun? · Ich wäre dir sehr dankbar für deine Meinung.",
        "hint_phrases_en": "Ich brauche dringend deinen Rat · Stell dir vor, ich habe... · Einerseits... andererseits... · Was würdest du an meiner Stelle tun? · Ich wäre dir sehr dankbar für deine Meinung.",
        "hint_example": "Liebe Jana, ich muss dir unbedingt von meiner Situation erzählen und brauche wirklich deinen Rat. Ich habe ein tolles Jobangebot bekommen, bin aber noch unsicher.",
    },
    {
        "id": "hotel_reservierung",
        "formal": True,
        "subject_tr": "Otel rezervasyonu",
        "subject_en": "Hotel reservation",
        "task_tr": "Bir tatil için otel rezervasyonu yapmak istiyorsun. Otele resmi bir e-posta yaz.",
        "task_en": "You want to book a hotel for a holiday. Write a formal email to the hotel.",
        "points_tr": ["Hangi tarihlerde gelmek istediğini belirt", "Kaç kişilik oda istediğini belirt", "Oda tipini sor (kahvaltı dahil mi?)", "Fiyat sor"],
        "points_en": ["State which dates you want to stay", "Specify how many people", "Ask about room type (breakfast included?)", "Ask about the price"],
        "hint_structure": "Betreff: Zimmerreservierung\n\nSehr geehrte Damen und Herren,\n\nich möchte ein Zimmer in Ihrem Hotel reservieren...\n\n[Datum]\n[Personenzahl]\n[Zimmertyp/Fragen]\n[Preisanfrage]\n\nMit freundlichen Grüßen,\n[Ihr Name]",
        "hint_phrases_tr": "Ich möchte ein Zimmer für ... Nächte reservieren · vom ... bis zum ... · für ... Personen · Ist das Frühstück im Preis inbegriffen? · Wie hoch sind die Kosten pro Nacht?",
        "hint_phrases_en": "Ich möchte ein Zimmer für ... Nächte reservieren · vom ... bis zum ... · für ... Personen · Ist das Frühstück im Preis inbegriffen? · Wie hoch sind die Kosten pro Nacht?",
        "hint_example": "Sehr geehrte Damen und Herren, ich möchte ein Doppelzimmer in Ihrem Hotel für zwei Personen vom 15. bis zum 20. Juli reservieren.",
    },
    {
        "id": "entschuldigung",
        "formal": False,
        "subject_tr": "Tartışma sonrası özür dileme",
        "subject_en": "Apologizing after an argument",
        "task_tr": "Arkadaşınla tartıştın ve pişmansın. Ona özür mektubu yaz.",
        "task_en": "You had an argument with your friend and regret it. Write them an apology email.",
        "points_tr": ["Yaşananlar için özür dile", "Hatalı olduğunu kabul et", "Nedenini açıkla", "Barışmayı öner"],
        "points_en": ["Apologize for what happened", "Admit you were wrong", "Explain the reason", "Suggest making up"],
        "hint_structure": "Betreff: Es tut mir leid\n\nLiebe(r) [Name],\n\nich schreibe dir, weil mir unser Streit sehr leidtut...\n\n[Entschuldigung]\n[Eigene Schuld eingestehen]\n[Erklärung]\n[Versöhnungsvorschlag]\n\nDein(e) [Name]",
        "hint_phrases_tr": "Es tut mir wirklich leid · Ich war unrecht / Ich hatte unrecht · Ich hätte das nicht sagen sollen · Kannst du mir vergeben? · Können wir uns treffen und reden?",
        "hint_phrases_en": "Es tut mir wirklich leid · Ich war unrecht / Ich hatte unrecht · Ich hätte das nicht sagen sollen · Kannst du mir vergeben? · Können wir uns treffen und reden?",
        "hint_example": "Liebe Sophie, ich muss dir unbedingt schreiben, weil mir unser Streit wirklich sehr leidtut. Ich war ungerecht zu dir und das war falsch von mir.",
    },
    {
        "id": "urlaub_bericht",
        "formal": False,
        "subject_tr": "Arkadaşa tatil hakkında yazma",
        "subject_en": "Writing to a friend about your holiday",
        "task_tr": "Harika bir tatilden döndün. Arkadaşına tatil hakkında anlatan bir e-posta yaz.",
        "task_en": "You just returned from a great holiday. Write your friend an email telling them about it.",
        "points_tr": ["Nereye gittiğini söyle", "En çok ne yaptığını anlat", "Bir ilginç anın anlat", "Arkadaşını da davet et"],
        "points_en": ["Say where you went", "Describe what you did most", "Tell an interesting moment", "Invite your friend to come next time"],
        "hint_structure": "Betreff: Mein Urlaub war fantastisch!\n\nLiebe(r) [Name],\n\nich bin gerade aus dem Urlaub zurück und muss dir unbedingt davon erzählen!\n\n[Reiseziel]\n[Aktivitäten]\n[Besonderes Erlebnis]\n[Einladung]\n\nLiebe Grüße,\n[Dein Name]",
        "hint_phrases_tr": "Ich war in ... · Das Wetter war ... · Am schönsten fand ich ... · Einmal ist etwas Lustiges passiert: · Du musst unbedingt auch mal dorthin!",
        "hint_phrases_en": "Ich war in ... · Das Wetter war ... · Am schönsten fand ich ... · Einmal ist etwas Lustiges passiert: · Du musst unbedingt auch mal dorthin!",
        "hint_example": "Liebe Anna, ich bin gerade aus dem Urlaub in Österreich zurückgekommen und muss dir sofort davon erzählen – es war absolut fantastisch!",
    },
    {
        "id": "veranstaltung_absage",
        "formal": True,
        "subject_tr": "Etkinlik iptali bildirimi",
        "subject_en": "Notifying about event cancellation",
        "task_tr": "Planladığın bir etkinlik iptal oldu. Katılımcılara resmi bir e-posta yaz.",
        "task_en": "An event you organized has been cancelled. Write a formal email to the participants.",
        "points_tr": ["Etkinliğin iptal edildiğini duyur", "Sebebini açıkla", "Özür dile", "Alternatif sun veya yeni tarih belirt"],
        "points_en": ["Announce the event is cancelled", "Explain the reason", "Apologize", "Offer an alternative or new date"],
        "hint_structure": "Betreff: Absage der Veranstaltung am [Datum]\n\nSehr geehrte Damen und Herren,\n\nleider muss ich Ihnen mitteilen, dass...\n\n[Grund]\n[Entschuldigung]\n[Alternativer Vorschlag]\n\nMit freundlichen Grüßen,\n[Ihr Name]",
        "hint_phrases_tr": "Leider muss ich Ihnen mitteilen, dass... · Aufgrund von ... musste ich leider... · Ich entschuldige mich herzlich für... · Als Alternative schlage ich vor... · Ich hoffe auf Ihr Verständnis.",
        "hint_phrases_en": "Leider muss ich Ihnen mitteilen, dass... · Aufgrund von ... musste ich leider... · Ich entschuldige mich herzlich für... · Als Alternative schlage ich vor... · Ich hoffe auf Ihr Verständnis.",
        "hint_example": "Sehr geehrte Damen und Herren, leider muss ich Ihnen mitteilen, dass die geplante Veranstaltung vom 20. Mai abgesagt werden muss.",
    },
    {
        "id": "krankmeldung",
        "formal": True,
        "subject_tr": "İşverene hastalık bildirimi",
        "subject_en": "Sick leave notification to employer",
        "task_tr": "Hasta olduğun için işe gidemiyorsun. İşverene resmi bir e-posta yaz.",
        "task_en": "You are sick and cannot come to work. Write a formal email to your employer.",
        "points_tr": ["Hasta olduğunu bildir", "Kaç gün işe gelemeyeceğini belirt", "Acil işlerin için çözüm öner", "Doktor raporu göndereceğini belirt"],
        "points_en": ["Inform them you are sick", "State how many days you will be absent", "Suggest a solution for urgent tasks", "Mention you will send a medical certificate"],
        "hint_structure": "Betreff: Krankmeldung\n\nSehr geehrte(r) Herr/Frau [Name],\n\nleider muss ich Ihnen mitteilen, dass ich krank bin und...\n\n[Zeitraum]\n[Lösung für dringende Aufgaben]\n[Attest]\n\nMit freundlichen Grüßen,\n[Ihr Name]",
        "hint_phrases_tr": "Leider bin ich erkrankt und kann nicht zur Arbeit kommen · Ich werde voraussichtlich ... Tage fehlen · Meine dringenden Aufgaben kann ... übernehmen · Das ärztliche Attest sende ich Ihnen zu · Ich bitte um Ihr Verständnis.",
        "hint_phrases_en": "Leider bin ich erkrankt und kann nicht zur Arbeit kommen · Ich werde voraussichtlich ... Tage fehlen · Meine dringenden Aufgaben kann ... übernehmen · Das ärztliche Attest sende ich Ihnen zu · Ich bitte um Ihr Verständnis.",
        "hint_example": "Sehr geehrte Frau Weber, leider muss ich Ihnen mitteilen, dass ich heute krank bin und nicht zur Arbeit kommen kann.",
    },
    {
        "id": "umzug_hilfe",
        "formal": False,
        "subject_tr": "Arkadaştan taşınmada yardım isteme",
        "subject_en": "Asking a friend to help with moving",
        "task_tr": "Yeni bir eve taşınıyorsun ve arkadaşından yardım istiyorsun. Ona e-posta yaz.",
        "task_en": "You are moving to a new apartment and need your friend's help. Write them an email.",
        "points_tr": ["Taşındığını ve yardım istediğini söyle", "Ne zaman taşınacağını belirt", "Ne tür yardıma ihtiyacın olduğunu açıkla", "Karşılığında ne yapacağını söyle (yemek ısmarlamak vs.)"],
        "points_en": ["Say you're moving and need help", "State when the move is", "Explain what kind of help you need", "Say what you'll offer in return (e.g. pizza)"],
        "hint_structure": "Betreff: Kannst du mir beim Umzug helfen?\n\nLiebe(r) [Name],\n\nich habe eine tolle Neuigkeit: Ich ziehe um!\n\n[Datum]\n[Art der Hilfe]\n[Angebot als Dankeschön]\n\nLiebe Grüße,\n[Dein Name]",
        "hint_phrases_tr": "Ich ziehe am ... um · Ich brauche Hilfe beim Tragen · Es dauert nicht lange · Als Dankeschön lade ich dich zu Pizza ein · Du wärst mir eine riesige Hilfe!",
        "hint_phrases_en": "Ich ziehe am ... um · Ich brauche Hilfe beim Tragen · Es dauert nicht lange · Als Dankeschön lade ich dich zu Pizza ein · Du wärst mir eine riesige Hilfe!",
        "hint_example": "Lieber Max, ich habe eine Neuigkeit: Ich ziehe nächsten Samstag in eine neue Wohnung um und würde mich sehr freuen, wenn du mir helfen könntest!",
    },
    {
        "id": "produkt_reklamation",
        "formal": True,
        "subject_tr": "Hatalı ürün için şikayet",
        "subject_en": "Complaint about a defective product",
        "task_tr": "Online sipariş ettiğin bir ürün hasarlı geldi. Müşteri hizmetlerine resmi bir e-posta yaz.",
        "task_en": "A product you ordered online arrived damaged. Write a formal email to customer service.",
        "points_tr": ["Ürünü ve sipariş numarasını belirt", "Sorunun ne olduğunu açıkla", "Ne istediğini belirt (iade, değişim)", "En kısa sürede çözüm talep et"],
        "points_en": ["Mention the product and order number", "Describe the problem", "State what you want (refund or exchange)", "Request a quick solution"],
        "hint_structure": "Betreff: Reklamation – Bestellnummer [XXX]\n\nSehr geehrte Damen und Herren,\n\nam [Datum] habe ich bei Ihnen ... bestellt (Bestellnummer: ...).\n\n[Problem beschreiben]\n[Lösung verlangen]\n[Frist setzen]\n\nMit freundlichen Grüßen,\n[Ihr Name]",
        "hint_phrases_tr": "Am ... habe ich ... bestellt · Das Produkt ist leider beschädigt angekommen · Ich bitte Sie um eine Rückerstattung / einen Umtausch · Ich erwarte Ihre Antwort bis zum ... · Anbei sende ich Ihnen Fotos.",
        "hint_phrases_en": "Am ... habe ich ... bestellt · Das Produkt ist leider beschädigt angekommen · Ich bitte Sie um eine Rückerstattung / einen Umtausch · Ich erwarte Ihre Antwort bis zum ... · Anbei sende ich Ihnen Fotos.",
        "hint_example": "Sehr geehrte Damen und Herren, am 10. März habe ich in Ihrem Online-Shop einen Laptop bestellt (Bestellnummer: 12345). Leider ist das Gerät beschädigt angekommen.",
    },
    {
        "id": "arzt_verschieben",
        "formal": True,
        "subject_tr": "Doktor randevusunu erteleme",
        "subject_en": "Rescheduling a doctor's appointment",
        "task_tr": "Doktor randevuna gidemeyeceksin. Kliniği arayamıyorsun, e-posta yaz.",
        "task_en": "You cannot make it to your doctor's appointment. You can't call, so write an email.",
        "points_tr": ["Randevunu ve tarihini belirt", "Neden gidemediğini açıkla", "Yeni bir randevu tarih öner", "Anlayış için teşekkür et"],
        "points_en": ["Mention your appointment and the date", "Explain why you can't come", "Suggest a new appointment date", "Thank them for understanding"],
        "hint_structure": "Betreff: Terminverschiebung am [Datum]\n\nSehr geehrte Damen und Herren,\n\nich habe am [Datum] einen Termin bei Ihnen...\n\n[Absagegrund]\n[Neuer Terminvorschlag]\n[Dankeschön]\n\nMit freundlichen Grüßen,\n[Ihr Name]",
        "hint_phrases_tr": "Leider kann ich meinen Termin am ... nicht wahrnehmen · Da ich an diesem Tag ... · Wäre es möglich, den Termin auf ... zu verschieben? · Ich danke Ihnen für Ihr Verständnis.",
        "hint_phrases_en": "Leider kann ich meinen Termin am ... nicht wahrnehmen · Da ich an diesem Tag ... · Wäre es möglich, den Termin auf ... zu verschieben? · Ich danke Ihnen für Ihr Verständnis.",
        "hint_example": "Sehr geehrte Damen und Herren, leider kann ich meinen Termin am 15. April nicht wahrnehmen, da ich an diesem Tag beruflich verhindert bin.",
    },
    {
        "id": "dankeschoen_besuch",
        "formal": False,
        "subject_tr": "Ziyaret sonrası arkadaşa teşekkür",
        "subject_en": "Thanking a friend after a visit",
        "task_tr": "Arkadaşın seni ziyaret etti ve harika zaman geçirdiniz. Teşekkür e-postası yaz.",
        "task_en": "Your friend visited you and you had a great time. Write a thank-you email.",
        "points_tr": ["Ziyaret için teşekkür et", "En çok ne yaşadığınızı anlat", "Bir şeyi çok beğendiğini söyle", "Karşılıklı ziyareti teklif et"],
        "points_en": ["Thank them for the visit", "Describe your favourite moment", "Say something you especially liked", "Suggest visiting them in return"],
        "hint_structure": "Betreff: Danke für deinen Besuch!\n\nLiebe(r) [Name],\n\nich wollte mich noch einmal herzlich für deinen Besuch bedanken!\n\n[Schönstes Erlebnis]\n[Was dir besonders gefallen hat]\n[Gegenbesuch vorschlagen]\n\nBis bald!\n[Dein Name]",
        "hint_phrases_tr": "Vielen Dank für deinen tollen Besuch! · Es hat mir so viel Spaß gemacht · Besonders gefallen hat mir ... · Ich freue mich schon auf meinen Gegenbesuch bei dir! · Es war wirklich schön!",
        "hint_phrases_en": "Vielen Dank für deinen tollen Besuch! · Es hat mir so viel Spaß gemacht · Besonders gefallen hat mir ... · Ich freue mich schon auf meinen Gegenbesuch bei dir! · Es war wirklich schön!",
        "hint_example": "Liebe Lena, ich wollte mich noch einmal ganz herzlich für deinen Besuch letztes Wochenende bedanken – ich hatte eine tolle Zeit mit dir!",
    },
    {
        "id": "wohnungssuche",
        "formal": True,
        "subject_tr": "Kiralık daire ilanına yanıt verme",
        "subject_en": "Responding to an apartment rental ad",
        "task_tr": "İnternet'te bir kiralık daire ilanı gördün. Ev sahibine resmi e-posta yaz.",
        "task_en": "You saw an apartment rental ad online. Write a formal email to the landlord.",
        "points_tr": ["Kendini kısaca tanıt", "İlanla ilgilendiğini belirt", "Birkaç soru sor (evcil hayvan, ortak giderler vs.)", "Görüşme talep et"],
        "points_en": ["Briefly introduce yourself", "Express interest in the ad", "Ask a few questions (pets, utility costs, etc.)", "Request a viewing appointment"],
        "hint_structure": "Betreff: Anfrage zur Wohnung – [Adresse]\n\nSehr geehrte(r) Herr/Frau [Name],\n\nich habe Ihre Anzeige gelesen und interessiere mich sehr für die Wohnung.\n\n[Kurzvorstellung]\n[Fragen]\n[Besichtigungswunsch]\n\nMit freundlichen Grüßen,\n[Ihr Name]",
        "hint_phrases_tr": "Ich habe Ihre Anzeige auf ... gesehen · Ich bin ... und suche eine Wohnung ab ... · Sind Haustiere erlaubt? · Wie hoch sind die Nebenkosten? · Wäre eine Besichtigung möglich?",
        "hint_phrases_en": "Ich habe Ihre Anzeige auf ... gesehen · Ich bin ... und suche eine Wohnung ab ... · Sind Haustiere erlaubt? · Wie hoch sind die Nebenkosten? · Wäre eine Besichtigung möglich?",
        "hint_example": "Sehr geehrter Herr Bauer, ich habe Ihre Anzeige auf ImmobilienScout gelesen und interessiere mich sehr für die angebotene Zweizimmerwohnung.",
    },
    {
        "id": "veranstaltung_einladen",
        "formal": False,
        "subject_tr": "Arkadaşları bir etkinliğe davet etme",
        "subject_en": "Inviting friends to an event",
        "task_tr": "Evinde küçük bir parti veriyorsun. Arkadaşlarını davet etmek için e-posta yaz.",
        "task_en": "You are hosting a small party at home. Write an email to invite your friends.",
        "points_tr": ["Etkinliği duyur", "Ne zaman ve nerede olduğunu belirt", "Ne getirmelerini iste (yiyecek, içecek vs.)", "Cevap vermelerini iste"],
        "points_en": ["Announce the event", "State when and where it is", "Ask them to bring something", "Ask them to confirm attendance"],
        "hint_structure": "Betreff: Party bei mir – Ihr seid eingeladen!\n\nLiebe alle,\n\nich lade euch herzlich zu einer kleinen Party ein!\n\n[Wann und wo]\n[Was mitbringen]\n[Um Rückmeldung bitten]\n\nBis dann!\n[Dein Name]",
        "hint_phrases_tr": "Ich lade euch herzlich ein · Am [Datum] um [Uhrzeit] · Bitte bringt ... mit · Gebt mir bitte bis [Datum] Bescheid · Ich freue mich auf euch!",
        "hint_phrases_en": "Ich lade euch herzlich ein · Am [Datum] um [Uhrzeit] · Bitte bringt ... mit · Gebt mir bitte bis [Datum] Bescheid · Ich freue mich auf euch!",
        "hint_example": "Liebe Freunde, ich möchte euch herzlich zu einer kleinen Party bei mir einladen! Sie findet am Samstag, den 10. Juni, ab 19 Uhr statt.",
    },
    {
        "id": "bibliothek_verlaengerung",
        "formal": True,
        "subject_tr": "Kütüphane kitap ödünç süresini uzatma",
        "subject_en": "Extending a library book loan",
        "task_tr": "Kütüphaneden ödünç aldığın kitabı bitiremedin. Süreyi uzatmak için e-posta yaz.",
        "task_en": "You haven't finished the library book you borrowed. Write an email to extend the loan.",
        "points_tr": ["Kitabın adını ve ödünç tarihini belirt", "Neden bitiremediğini açıkla", "Kaç gün daha istediğini belirt", "Teşekkür et"],
        "points_en": ["State the book title and borrowing date", "Explain why you haven't finished it", "Say how many more days you need", "Thank them"],
        "hint_structure": "Betreff: Verlängerung der Ausleihe – [Buchtitel]\n\nSehr geehrte Damen und Herren,\n\nich habe am [Datum] das Buch '[Titel]' ausgeliehen.\n\n[Erklärung]\n[Wie viele Tage]\n[Dankeschön]\n\nMit freundlichen Grüßen,\n[Ihr Name]",
        "hint_phrases_tr": "Ich habe das Buch ... ausgeliehen · Leider konnte ich es noch nicht fertiglesen, da... · Ich bitte um eine Verlängerung um ... Tage · Vielen Dank für Ihr Entgegenkommen.",
        "hint_phrases_en": "Ich habe das Buch ... ausgeliehen · Leider konnte ich es noch nicht fertiglesen, da... · Ich bitte um eine Verlängerung um ... Tage · Vielen Dank für Ihr Entgegenkommen.",
        "hint_example": "Sehr geehrte Damen und Herren, ich habe am 1. Mai das Buch 'Der Vorleser' in Ihrer Bibliothek ausgeliehen und bitte um eine Verlängerung der Ausleihfrist.",
    },
    {
        "id": "kurs_abmeldung",
        "formal": True,
        "subject_tr": "Kurstan çıkma bildirimi",
        "subject_en": "Withdrawing from a course",
        "task_tr": "Kayıt olduğun bir kurstan ayrılmak istiyorsun. Okula resmi e-posta yaz.",
        "task_en": "You want to withdraw from a course you enrolled in. Write a formal email to the school.",
        "points_tr": ["Hangi kursa kayıtlı olduğunu belirt", "Neden ayrılmak istediğini açıkla", "Son katılım tarihini sor", "Ücret iadesi olup olmadığını sor"],
        "points_en": ["State which course you are enrolled in", "Explain why you want to withdraw", "Ask about your last attendance date", "Ask if a refund is possible"],
        "hint_structure": "Betreff: Abmeldung vom Kurs [Kursname]\n\nSehr geehrte Damen und Herren,\n\nich bin für den Kurs ... angemeldet und möchte mich leider abmelden.\n\n[Grund]\n[Letzte Teilnahme]\n[Rückerstattungsfrage]\n\nMit freundlichen Grüßen,\n[Ihr Name]",
        "hint_phrases_tr": "Ich möchte mich vom Kurs abmelden · Leider muss ich den Kurs beenden, weil... · Ab wann gilt meine Abmeldung? · Ist eine Rückerstattung der Kursgebühr möglich? · Ich bedanke mich für die bisherige Zusammenarbeit.",
        "hint_phrases_en": "Ich möchte mich vom Kurs abmelden · Leider muss ich den Kurs beenden, weil... · Ab wann gilt meine Abmeldung? · Ist eine Rückerstattung der Kursgebühr möglich? · Ich bedanke mich für die bisherige Zusammenarbeit.",
        "hint_example": "Sehr geehrte Damen und Herren, ich bin seit Oktober für den Deutschkurs B1 bei Ihnen angemeldet und muss mich leider abmelden.",
    },
]
# fmt: on


def _lang() -> str:
    return st.session_state.get("ui_lang", "tr")


def _init() -> None:
    defaults = {
        "brief_idx": 0,
        "brief_hint_level": 0,
        "brief_feedback": None,
        "brief_checked": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


def render(words: list, custom_words: list) -> None:
    _init()

    prompt = PROMPTS[st.session_state.brief_idx % len(PROMPTS)]
    lang = _lang()

    # Task card
    is_formal = prompt["formal"]
    type_label = t("brief_type_formal") if is_formal else t("brief_type_informal")
    type_color = "#3b82f6" if is_formal else "#8b5cf6"
    subject = prompt["subject_tr"] if lang == "tr" else prompt["subject_en"]
    task = prompt["task_tr"] if lang == "tr" else prompt["task_en"]
    points = prompt["points_tr"] if lang == "tr" else prompt["points_en"]

    col_card, col_ctrl = st.columns([5, 1])
    with col_card:
        points_html = "".join(f"<li>{p}</li>" for p in points)
        st.markdown(
            f"<div style='padding:1.2rem 1.4rem;background:#f8fafc;"
            f"border:1px solid #e2e8f0;border-radius:12px;'>"
            f"<div style='display:flex;align-items:center;gap:0.6rem;margin-bottom:0.6rem'>"
            f"<span style='background:{type_color}18;color:{type_color};font-size:0.75rem;"
            f"font-weight:600;padding:2px 10px;border-radius:20px;border:1px solid {type_color}40'>"
            f"{type_label}</span>"
            f"<span style='font-weight:600;color:#1e293b'>{subject}</span></div>"
            f"<p style='color:#475569;margin:0 0 0.7rem'>{task}</p>"
            f"<ul style='margin:0;padding-left:1.3rem;color:#334155'>{points_html}</ul>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col_ctrl:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔄", use_container_width=True, help=t("brief_btn_new"), key="brief_new"):
            new_idx = (st.session_state.brief_idx + random.randint(1, len(PROMPTS) - 1)) % len(PROMPTS)
            st.session_state.brief_idx = new_idx
            st.session_state.brief_hint_level = 0
            st.session_state.brief_feedback = None
            st.session_state.brief_checked = False
            st.rerun()

    st.markdown("---")

    # Text area
    user_text = st.text_area(
        t("brief_text_label"),
        placeholder=t("brief_text_placeholder"),
        height=250,
        key=f"brief_text_{st.session_state.brief_idx}",
    )

    # Hint + Check
    col_hint, col_check = st.columns(2)
    with col_hint:
        level = st.session_state.brief_hint_level
        if level == 0:
            if st.button(f"💡 {t('brief_hint_btn_structure')}", use_container_width=True, key="brief_h1"):
                st.session_state.brief_hint_level = 1
                st.rerun()
        elif level == 1:
            if st.button(f"📝 {t('brief_hint_btn_phrases')}", use_container_width=True, key="brief_h2"):
                st.session_state.brief_hint_level = 2
                st.rerun()
        elif level == 2:
            if st.button(f"✍️ {t('brief_hint_btn_example')}", use_container_width=True, key="brief_h3"):
                st.session_state.brief_hint_level = 3
                st.rerun()
        else:
            st.button(f"✅ {t('bild_hint_all_shown')}", use_container_width=True, disabled=True, key="brief_hall")

    with col_check:
        ai = get_ai_service()
        if st.button(
            f"✅ {t('bild_btn_check')}",
            use_container_width=True,
            type="primary",
            disabled=st.session_state.brief_checked or not user_text.strip(),
            key="brief_check",
        ):
            if not ai.can_generate():
                st.error(t("bild_ai_required"))
            else:
                task_context = f"{task} ({', '.join(points)})"
                with st.spinner(t("bild_spinner")):
                    feedback = ai.check_brief_schreiben(
                        task_context=task_context,
                        user_text=user_text.strip(),
                        is_formal=is_formal,
                    )
                if feedback:
                    st.session_state.brief_feedback = feedback
                    st.session_state.brief_checked = True
                    add_xp(25)
                    persist_current_user()
                    st.rerun()
                else:
                    st.error(t("bild_check_error"))

    # Progressive hints
    _render_hints(prompt)

    # Feedback
    if st.session_state.brief_feedback:
        _render_feedback(st.session_state.brief_feedback)
        if st.button(f"🔄 {t('brief_btn_next')}", use_container_width=True, type="primary", key="brief_next"):
            new_idx = (st.session_state.brief_idx + 1) % len(PROMPTS)
            st.session_state.brief_idx = new_idx
            st.session_state.brief_hint_level = 0
            st.session_state.brief_feedback = None
            st.session_state.brief_checked = False
            st.rerun()


def _render_hints(prompt: dict) -> None:
    level = st.session_state.brief_hint_level
    if level < 1:
        return
    lang = _lang()

    if level >= 1:
        with st.expander(f"💡 {t('brief_hint_structure')}", expanded=True):
            st.markdown(
                f"<div style='font-family:monospace;white-space:pre-wrap;background:#f1f5f9;"
                f"padding:0.8rem;border-radius:8px;font-size:0.88rem;color:#334155'>"
                f"{prompt['hint_structure']}</div>",
                unsafe_allow_html=True,
            )

    if level >= 2:
        with st.expander(f"📝 {t('brief_hint_phrases')}", expanded=True):
            phrases_raw = prompt["hint_phrases_tr"] if lang == "tr" else prompt["hint_phrases_en"]
            phrases = [p.strip() for p in phrases_raw.split("·")]
            tag_html = " ".join(
                f"<span style='display:inline-block;background:#ede9fe;color:#5b21b6;"
                f"padding:3px 10px;border-radius:16px;font-size:0.85rem;margin:2px'>{p}</span>"
                for p in phrases if p
            )
            st.markdown(tag_html, unsafe_allow_html=True)

    if level >= 3:
        with st.expander(f"✍️ {t('bild_hint_example')}", expanded=True):
            st.markdown(
                f"<div style='padding:0.7rem 1rem;background:#f0fdf4;border-left:3px solid #22c55e;"
                f"border-radius:8px;font-style:italic;color:#166534'>{prompt['hint_example']}</div>",
                unsafe_allow_html=True,
            )


def _render_feedback(fb: dict) -> None:
    grade = fb.get("grade", 3)
    grade_colors = {1: "#22c55e", 2: "#84cc16", 3: "#eab308", 4: "#f97316", 5: "#ef4444", 6: "#dc2626"}
    grade_labels = {1: "Sehr gut", 2: "Gut", 3: "Befriedigend", 4: "Ausreichend", 5: "Mangelhaft", 6: "Ungenügend"}
    color = grade_colors.get(grade, "#64748b")
    label = grade_labels.get(grade, "")

    st.markdown("---")
    st.markdown(f"### 🎓 {t('bild_feedback_title')}")

    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(
            f"<div style='text-align:center;padding:1.2rem 0.5rem;background:{color}18;"
            f"border:2px solid {color};border-radius:12px'>"
            f"<div style='font-size:2.8rem;font-weight:800;color:{color}'>{grade}</div>"
            f"<div style='font-size:0.85rem;font-weight:600;color:{color};margin-top:4px'>{label}</div>"
            f"</div>",
            unsafe_allow_html=True,
        )
    with col2:
        errors = fb.get("grammar_errors", "")
        st.markdown(f"**{t('bild_fb_grammar')}**")
        if errors and errors.lower() not in ("keine fehler", "no errors", "-"):
            st.warning(errors)
        else:
            st.success(f"✅ {t('bild_fb_no_errors')}")
    with col3:
        style = fb.get("style_feedback", "")
        st.markdown(f"**{t('brief_fb_style')}**")
        if style:
            st.info(style)

    if fb.get("content_feedback"):
        st.markdown(
            f"<div style='padding:0.7rem 1rem;background:#fefce8;border-left:3px solid #eab308;"
            f"border-radius:8px;margin-top:0.5rem'>"
            f"<strong>📋 {t('brief_fb_content')}</strong> {fb['content_feedback']}</div>",
            unsafe_allow_html=True,
        )

    if fb.get("example"):
        st.markdown(
            f"<div style='padding:0.7rem 1rem;background:#f0fdf4;border-left:3px solid #22c55e;"
            f"border-radius:8px;margin-top:0.5rem;font-style:italic'>"
            f"<strong>✍️ {t('bild_fb_example')}</strong> {fb['example']}</div>",
            unsafe_allow_html=True,
        )

    if fb.get("summary"):
        st.markdown(f"> 💬 {fb['summary']}")

    st.success(f"⚡ +25 XP {t('bild_xp_earned')}")
