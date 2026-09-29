# Plan: upgrading adyatithi festival data from the Smṛti-Kaustubha (संवत्सरदीधितिः)

Status: **PLAN ONLY (nothing implemented yet)**. Source text: OCR of *Smṛti-Kaustubha* of Anantadeva (Nirṇaya-Sāgara, Bombay 1931, ed. W. L. Pansikar),
file [`source/ocr/smriti-kaustubha-1931.ocr.txt`](https://github.com/stotrasamhita/smriti-kaustubham/blob/master/source/ocr/smriti-kaustubha-1931.ocr.txt) in `stotrasamhita/smriti-kaustubham` (620 OCR pages, `### NNN.json` markers). Working notes: [`smriti_kaustubha_notes.md`](smriti_kaustubha_notes.md).

Targets:
- **Data**: `jyotisham/adyatithi` TOML files (shlokas, references, timing fixes, new festival files).
- **Code**: `jyotisham/jyotisha` (only where a rule cannot be expressed with the current TOML schema).

---------------------------------------------------------------------------------------------------

## 0. Conventions used in this plan

- **Page numbers** are the *printed* book pages (Devanagari page numbers in the running head), written `p.NNN`.
  In the OCR file, printed page ≈ `json − 19` for Chaitra (json 104 = p.85) and ≈ `json − 17` from Vaishakha onward
  (json 350 = p.333, json 472 = p.455). Cite as `references_primary = ["Smriti Kaustubha p.NNN"]`.
- **Month/tithi numbers** follow adyatithi (amānta): month 1 = Chaitra … 12 = Phālguna; tithi 1–15 śukla, 16–30 kṛṣṇa
  (so "05/19" = Śrāvaṇa kṛṣṇa caturthī). Where the book speaks pūrṇimānta (e.g. "कार्तिक-कृष्ण" inside the Āśvina chapter),
  the date is converted to amānta here.
- **Status legend**: `ADD-SH` = add shlokas/refs to an existing entry; `FIX` = correct existing timing/data;
  `NEW` = new festival file; `NEW-CODE` = needs a jyotisha code change; `SKIP` = deliberately left out in this pass.
- **Complexity**: S = plain tithi/nakshatra rule; M = needs `intersection_groups`/`vaara`/`angas` or a kaala/priority nuance;
  H = needs new code (graha positions, bhadrā, conditional fall-backs, etc.).
- Shlokas below are given in **corrected** form (OCR fixed) where the correction was obvious. Anything marked `[?]`
  must be verified against a clean scan (see §2).

Scope of this pass (per request): the month-wise *saṃvatsara-dīdhiti* (Chaitra … Phālguna, Adhika-māsa,
saura/sāvana/bārhaspatya/nākṣatra/yoga sections: book pp.83–565). Ekādaśī-specific material, long vrata-kathās,
prayoga/udyāpana minutiae, kuṇḍa geometry, tīrtha māhātmyas, Kali-varjya and the Āśauca-dīdhiti are skipped.
The Tithi-dīdhiti (general tithi rules, pp.1–82) is deferred to a second pass (§9).

---------------------------------------------------------------------------------------------------

## 1. Executive summary

| Bucket | Count (approx.) | Notes |
|---|---|---|
| Existing entries to enrich with SK shlokas/refs (`ADD-SH`) | ~150 | Many important festivals currently have **no shlokas at all** (e.g. yugAdiH, dUrvASTamI, durgASTamI, mahAnavamI, kAlabhairavASTamI, dIpAvalI, hOli, ziva-zayanOtsavaH, tripurOtsavaH, karaka-caturthI, all upAkarma entries). |
| Timing/data corrections (`FIX`) | ~35 | kaala/priority changes backed by explicit SK nirṇaya; three "snāna-pūrti" dates; mahAlakṣmī-vrata start/end; a few wrong tithis/refs. |
| New festivals, simple (`NEW`, S/M) | ~90 | Includes whole families (Nāgarakhaṇḍa kalpādis, damanaka tithis, pavitrāropaṇa tithis, 12 saṅkrānti-dānas, pūrṇimā+nakṣatra dānas). |
| New festivals needing code (`NEW-CODE`, H) | ~15 | bhadrā/viṣṭi-aware Holikā & Rakṣābandhana, graha-in-nakṣatra yogas (mahājyeṣṭhī, mahākārtikī-guru, padmaka), rohiṇī-override Jayantī, etc. |
| OCR error patterns logged | ~250 individual fixes + ~10 pages needing re-OCR | See §2. |

Suggested order: §3 infrastructure → §4 FIX list → month-wise ADD-SH (cheap, high value) → simple NEW → NEW-CODE.

---------------------------------------------------------------------------------------------------

## 2. OCR quality: policy, recurring errors, pages to re-check

### 2.1 Policy
1. Never paste OCR text into TOML unedited. Every shloka goes through: (a) metre/sandhi sanity check, (b) comparison with the
   same verse in another nibandha already quoted in adyatithi (Nirṇaya-sindhu, Dharma-sindhu, Vaidyanātha-dīkṣitīyam,
   Puruṣārtha-cintāmaṇi) when available, (c) a clean scan of the 1931 edition (archive.org / DLI) for anything flagged `[?]`.
2. Add a small helper script (optional, in a scratch location, not in the repo) that applies the regex fixes in §2.2 and
   highlights residual non-Devanagari characters (`?`, `h`, `.`, `ऱ्या`, digits in words).
3. Record the corrected text only; do not keep OCR variants in data files.

### 2.2 Systematic OCR error patterns (fix globally, then eyeball)
| OCR | Correct | Examples |
|---|---|---|
| `ऱ्या`, `ाऱ्या`, `य॑`, `र्य` in *arghya* | `र्घ्य` / `र्घ्यं` | गृहाणाऱ्या → गृहाणार्घ्यं; चन्द्रायाय॑ → चन्द्रायार्घ्यं; अयं (for अर्घ्यं) |
| `सान`, `सात्वा`, `साति`, `माया`, `नान` | `स्नान`, `स्नात्वा`, `स्नाति`, `स्नाया`, `स्नान` | "सानं कृत्वा" → "स्नानं कृत्वा" |
| `पूर्वविद्धव`, `विद्वैव` | `पूर्वविद्धैव`, `विद्धैव` | throughout nirṇayas |
| `चतुझं` | `चतुर्थ्यां` | p.119, p.171, p.215 |
| `बढच`, `बह्मचाः` | `बह्वृच` | upākarma pp.153–158 |
| `दयात्`, `दद्यात` split | `दद्यात्` | passim |
| `तयाप्ति`, `तयापिन्य` | `तद्व्याप्ति`, `तद्व्यापिन्य` | passim |
| `दना` | `दध्ना` | pp.92, 486 |
| `भक्या`, `शक्या`, `भच्या`, `शच्या` | `भक्त्या`, `शक्त्या` | passim |
| `पाझे`, `पाने` (when "in Padma") | `पाद्मे` | passim |
| `ब्राझे` | `ब्राह्मे` | passim |
| `जत्वा`, `तुत्वा` | `जप्त्वा`, `हुत्वा` | passim |
| `राशी`, `राशा` (royal) | `राज्ञी`, `राज्ञा` | p.124, p.439 |
| `ताने`, `तानं` (metal) | `ताम्रे`, `ताम्रं` | passim |
| `मुयात्`, `मामुयात्` | `आप्नुयात्` / `प्राप्नुयात्` | passim |
| `ह्र`/`हृ` confusions, `जो०`, `जके`, `जर्छ` | `जङ्घे` | aṅga-pūjā lists |
| `पू.`, `प्र.`, `०` abbreviations | expand from context | pūjā lists |
| `मे`/`मॅ` for `मेष` etc. | context | p.540 (saṅkrānti-dāna) |

### 2.3 Page-specific corrections (samples; full list in [the working notes](smriti_kaustubha_notes.md) – carry into each TOML edit)
- p.85 जगब्रह्मा→जगद्ब्रह्मा; समयं→समग्रं; p.86 सा-त्पात→सोत्पात; p.88 प्रजशिवान्→प्रजज्ञिवान्, यहिनादाक्कल्प→यद्दिनात्कल्प;
  p.90 द्रुतं→व्रतं, भक्षयेन→भक्षयेन्न, मधोवीं→मधोर्देवीं.
- p.92 गणपतेदमन→गणपतेर्दमन; haya-pūjā gandharva list: "प्रत्यु[युक्तश्च" [?], "ापिकाभिश्च"→"पूपिकाभिश्च" [?].
- p.94 भसीकृत्वा→भस्मीकृत्वा; मयों→मर्त्यो; कुम्भीपाकेपु→कुम्भीपाकेषु.
- p.97–99 homa lists: इन्हें→इन्द्रं, नितिं→निर्ऋतिं, वजं→वज्रं, खरं→खड्गं.
- p.101 सहौस्तु→सहस्रैस्तु; p.103 कालते→कलयते; वेघोषेण→वेदघोषेण; शुद्धोकेन→शुद्धोदकेन.
- p.104 the Dīpikā list of pūrva-viddhā tithis is garbled: "तिथिVख्या सबहत्तपा च नवमी" → needs clean scan `[?]`.
- p.107 शतसूयग्रहैः→शतसूर्यग्रहैः; अग्रहकोटि→ग्रहकोटि; p.108 नाना व→नाम्ना च [?]; प्रेतिपारणम्→प्रतिपारणम्.
- p.109–111 यवैोमो→यवैर्होमो; बबक्षरमालया→बह्वक्षरमालया; यहीयते→यद्दीयते; संतप्यं→संतर्प्य; ढे शुक्ले→द्वे शुक्ले; जगुना→जह्नुना.
- p.113–116 पायलैः→पायसैः; नाप्य→स्नाप्य; अथावोभयोः→अथात्रोभयोः; तिथिादशी→तिथिर्द्वादशी; तीनैश्च→तीव्रैश्च;
  शुतानमुदकुम्भं→सान्नमुदकुम्भं; शस्या→शक्त्या.
- p.117 कञ्जनं/काजो→कञ्जं/कञ्जो; /जपूरकैः→बीजपूरकैः; बंदर्भक्ष्यैः→बदरैर्भक्ष्यैः [?].
- p.119–122 (Daśaharā stotra) हस्तः→हस्तर्क्षे; हरेढे→हरेद्दश; मूत्र्यै→मूर्त्यै; विषहव्यै→विषहन्त्र्यै; दुरितन्य→दुरितघ्न्यै;
  निलैपायै→निर्लेपायै; रोगा?→रोगस्थो [?]; दौर्यास्तु→गौर्यास्तु; गौॉरन्तरं→गौर्यन्तरं; कलशोधत्लोत्पला [?]; पादाज→पादाब्ज.
- p.124–137 (Vaṭa-sāvitrī) राशी भवेन्मय→राज्ञी भवेन्मर्त्ये; वटाले→वटमूले; लवयित्वा→लङ्घयित्वा; परिमेष्ठिने→परमेष्ठिने; वहिजाते→वह्निजाते.
- p.137–141 विवस्वानाम→विवस्वान्नाम; महिषनी→महिषघ्नी; ऐन्द्रीनानीं→ऐन्द्रीनाम्नीं; आभाकायेषु [?]; उयक्षरै→त्र्यक्षरैः; वय॑म्→वर्ज्यम्.
- p.143–147 वैयाले→वैयाघ्रे; समुंद्रथ्याहिवर्मणा→समुद्ग्रथ्याहिवर्मणा; वसेनामे→वसेद्ग्रामे; कोडरूपेण→क्रोडरूपेण; शरण→शरेण; तीवाणि→तीव्राणि.
- p.149–170 (Upākarma) श्रवणलंयुते→श्रवणसंयुते; विधीतै→विधीयते; कुर्युग्रह→कुर्युर्ग्रह; अवृष्टयोपधय→अवृष्ट्यौषधयः; अर्धरात्रादक्तुि→अर्धरात्रादर्वाक्तु; दौयिकी→औदयिकी; उपाकुत्तुि→उपाकुर्यात्तु.
- p.171–174 (Saṅkaṣṭa) त्रिनिर्माणैः [?]; कुश्माक्षता→कुङ्कुमाक्षता; विघ्नहर्ने→विघ्नहर्त्रे; भक्षयनिशि→भक्षयेन्निशि.
- p.191 जगदीजं→जगद्बीजं; त्रिविक्रनम्→त्रिविक्रमम्.
- p.201–202 सवैरूढैः→सविरूढैः; खजूरै रिकेलैश्च→खर्जूरैर्नारिकेलैश्च; धान्यकै रकैः→धान्यकैर्जीरकैः; हरेर्नाग्नि→हरेर्नाम्नि; प्रणतातिहरे→प्रणतार्तिहरे.
- p.215–216 कुत्तिस्मात्→कुर्यात्तस्मात्; पश्येन→पश्येन्न; सिहो→सिंहो.
- p.221–222 सप्तरन्जुश्च→सप्तरज्जुश्च; गृहामि→गृह्णामि; दाम्यहम्→ददाम्यहम्.
- p.228–231 दुर्वी/दूर्वी→दूर्वां; ऐन्द्रः पूजिता [?]; ज्येष्ठः महती→ज्येष्ठर्क्षे महती.
- p.237–238 स्वनी→स्वघ्नी; त्रिस्मृक→त्रिस्पृक्.
- p.250 वचुली→वञ्जुली; स्याहादशी→स्याद्द्वादशी; अभीएकाम्युपवसेइष्टौ→अभीष्टकाम्युपवसेदष्टौ; वेधैर्ह विरुद्भवैः→नैवेद्यैर्हविरुद्भवैः.
- p.254 शकमु.स्थापयेद्→शक्रमुत्थापयेद्.
- p.270–279 विभागहीनं→त्रिभागहीनं; बजेद्रविः→व्रजेद्रविः; ज्येभ्यः→शिष्येभ्यः; पित्रर्मी→पित्र्यर्क्षे; वाीणसस्य→वार्ध्रीणसस्य.
- **p.283 (json 300) arghya paragraph of Kapilā-ṣaṣṭhī is badly garbled → re-OCR the whole page.**
- p.287 नमुद्धर→समुद्धर; भुफिमुक्तिप्रडो→भुक्तिमुक्तिप्रदो.
- p.294 धवलनिन्बधे→धवलनिबन्धे; तावदाज्यभङ्गः→तावद्राज्यभङ्गः; कारूयेन→कार्त्स्न्येन.
- p.308–310 पूजयित्वाभे→पूजयित्वार्द्रभे; बोधयेहेवी→बोधयेद्देवीं; दुर्वेद्युः→पूर्वेद्युः.
- p.325–327 दशस्यां→दशम्यां; निह रावणे→निहते रावणे; त्याच्यानां→प्राच्यानां.
- p.352–353 श्रवणः यदा→श्रवणर्क्षं यदा; तद्दिनः→तद्दिनर्क्षे; धरियर्जुन→धारिण्यर्जुन.
- p.358–361 समनं→समग्रं; व्यहस्मातास्तु→त्र्यहस्नातास्तु; दामोदराने सेनानीगर्गासहस्र→दामोदराग्रे … गवां सहस्र [?]; पमेनैकेन→पद्मेनैकेन.
- p.370–373 लक्ष्मीले→लक्ष्मीर्जले; सकपटक→सकण्टक; अग्निज्योती रवियोतिः→अग्निर्ज्योती रविर्ज्योतिः; हेना चामेन→हेम्ना चामेन.
- p.375–376 प्रबनीयात्→प्रबध्नीयात्; बेलिनामाख्य→बलिनामाख्य.
- p.427–432 वारें शुमालिनः→वारेंऽशुमालिनः; कश्यपाजझे→कश्यपाज्जज्ञे; मागशीर्षे पञ्चमेऽह्नि दशेऽह्नि→मार्गशीर्षे पञ्चदशेऽह्नि; शस्य→बुधस्य.
- p.439–442 सौंपधियुतै लैः→सर्वौषधियुतैर्जलैः; माधवावियुगं→माधवाङ्घ्रियुगं; किंचिभ्युदिते→किंचिदभ्युदिते; उष्णीं→उष्णीषं; कसरं→कृसरं.
- p.442–446 अधोदयः→अर्धोदयः; सूर्यस्या?दये→सूर्यस्योदये; ऽयम्बकं→त्र्यम्बकं.
- p.479–481 नतोपवासयोः→नक्तोपवासयोः; राज्यन्ते→रात्र्यन्ते; संतh→संतर्प्य; यदाजन्म→यद्यज्जन्म; विस्पृश्यां→त्रिस्पृशायां.
- p.513–519 मायाकोड→मायाक्रोड; द्विशीर्णे→द्विशीर्ष्णे; रक्षोभेमन्त्र→रक्षोघ्नमन्त्र; चूत.मयं→चूतमग्र्यं.
- p.540 saṅkrānti-dāna verse: `मॅपदानं`→`मेषदानं`, `हम्लानां`→`हर्म्याणां` [?]; p.552 the saṅkrānti–avatāra list is **missing tulā/vṛścika/dhanus lines** (edition or OCR gap) → check scan.
- p.557 षडक्षर/महाश्वेत mantra line garbled; p.559 simhastha-guru verses fine; p.565 मुने पञ्च→मुखे पञ्च; चतनः→चतस्रः.

### 2.4 Pages that are too garbled for direct use (re-OCR first)
json 300 (p.283), 460–461 (ardhodaya vrata aṅga lists), 478–491 (kuṇḍa geometry – skipped anyway), 557 (mantras),
583/599+ (Kali-varjya – skipped), 614–617 (pāṭhāntara appendix – useful for **variant readings**: consult when a verse is doubtful).

---------------------------------------------------------------------------------------------------

## 3. Cross-cutting infrastructure work (do first)

### 3.1 Data hygiene (adyatithi)
1. **Unify the reference string**: currently "Smriti Kaustubham p.NN", "Smriti Kaustubha p. NN", "Smriti Kaustubham NNN".
   Pick one (`Smriti Kaustubha p.NNN`) and migrate all 43 files.
2. **Fix wrong page citations** already in adyatithi:
   - `nRsiMha-dOlOtsavaH` cites p.90 → correct is **p.104**.
   - `gaurI~tRtIyA_or_saubhAgya-gaurI-vratam` cites p.89 → the Chaitra gaurī-vrata verse is p.89 (OK) but the tṛtīyā rule is p.90–91; recheck.
   - `mahAbharaNI` cites p.274 (OK). `prEta-caturdazI` cites p.371 (OK). `vasanta-zrI-paJcamI` cites "479" (add "p.").
3. **Existing unsourced shlokas that SK sources**: `kapila-SaSThI` shloka "प्रभाकर नमस्तुभ्यं…" = SK p.287 (Skānda, Prabhāsa-khaṇḍa); add ref.

### 3.2 jyotisha code capabilities needed (NEW-CODE)
The current `HinduCalendarEventTiming` already supports `intersection_groups` (tithi/nakshatra/yoga/karana/vaara/solar_nakshatra/nakshatra_pada),
`vaara`, `angas`, `adhika_maasa_handling`, kaalas incl. `रौहिणः` muhūrta names. Missing:

| # | Capability | Needed for |
|---|---|---|
| C1 | **Bhadrā/viṣṭi segmentation** (mukha 5 ghaṭī, kaṇṭha 1, hṛdaya 11, nābhi 4, kaṭi 6, puccha 3; direction rule) and a "avoid bhadrā / use bhadrā-puccha / after bhadrā-end" fall-back chain | Holikā (p.517–518), Rakṣābandhana (p.167), generic "भद्रायां द्वे न कर्तव्ये श्रावणी फाल्गुनी तथा" |
| C2 | **Graha-in-nakṣatra conditions** (Jupiter/Moon/Sun in a given nakṣatra, sun in *half* of a nakṣatra) | mahājyeṣṭhī (p.137), mahākārtikī (guru+candra in kṛttikā, p.406), padmaka (sun viśākhā + moon kṛttikā), kapilā-ṣaṣṭhī (sun in hasta), mahālakṣmī samāpana (sun in 2nd half of hasta = doṣa), gajacchāyā (sun in hasta) |
| C3 | **Conditional nakṣatra override** of kaala-vyāpti (rohiṇī-yuktā aṣṭamī beats niśītha-vyāpti; jyeṣṭhā-yuktā aṣṭamī for jyeṣṭhā-gaurī/mahālakṣmī; śravaṇa-yuktā daśamī for vijayā) | Janmāṣṭamī/Jayantī (p.181–187), jyeṣṭhā-vrata (p.231), aparājitā (p.352) |
| C4 | **Nakṣatra exclusion** ("…ज्येष्ठामूलं विवर्जयेत्") and **solar-month gating** (simha-ravi only, not kanyā; fall-back to previous kṛṣṇa aṣṭamī) | Dūrvāṣṭamī (p.229–230) |
| C5 | **Bhadrapada-fallback Jayantī** (if no rohiṇī-yoga on Śrāvaṇa k8, look at Bhādra k8) | Jayantī (p.194–195) |
| C6 | **"Next-day tithi ≥ N yāma" rules** (Holikā pratipat fall-back; Govardhana "त्रियामिका दर्शतिथिः…"; Śiva-rātri "trispṛśā") | p.374, p.518, p.483 |
| C7 | **Nakṣatra-upavāsa rule**: choose the day whose sunset (else niśītha) has the nakṣatra | generic nakṣatra vratas (p.562) |
| C8 | **Graha-yoga with 2 grahas in a rāśi** (Jupiter+Mars in Siṃha, Sun in Meṣa…) | Vaiśākha dvādaśī "vyatīpāta" (p.114) – LOW, can stay SKIP |
| C9 | **Solar-month + lunar-tithi conjunction** as a first-class condition (already possible via intersection? verify `solar` month in groups) | Mahāṣaṣṭhī (vṛścika + kārtika ś6 + bhauma), nāndīmukha-śrāddha (bhādra pūrṇimā in a month containing kanyā-saṅkrānti), ulkādāna (sun in tulā) |
| C10 | **Adhika-māsa policy audit** using SK p.525–529 lists (which rites are nija-only, adhika-only, both) | yugādi/manvādi śrāddha (both months), first upākarma (not in adhika), cāturmāsya śayana (not in adhika), etc. |

---------------------------------------------------------------------------------------------------

## 4. Consolidated FIX list (existing entries whose timing/data disagree with SK)

> **Deferred (decision, 2026-09-29):** these timing changes stay as notes for now. Other traditions (e.g. Smṛti-muktāphala, which many current entries follow) decide several of them differently, so SK alone is not a reason to change computed dates. Revisit per festival, recording which tradition each entry follows.

| id (month/tithi) | Current | SK says (page) | Action |
|---|---|---|---|
| `madana-trayOdazI` (01/13) | madhyāhna, no priority | kandarpa-vrata trayodaśī must be **pūrvaviddhā** (p.104, Dīpikā) | set `priority = "puurvaviddha"` |
| `nAga-paJcamI` (05/05) | no kaala/priority | **ṣaṣṭhī-yuktā (para)**: "पञ्चमी नागपूजायां कार्या षष्ठीसमन्विता" (p.149) | `priority = "paraviddha"` |
| `ziva-zayanOtsavaH` (04/15) | none | pūrvaviddhā: "रुद्रव्रतेषु सर्वेषु कर्तव्या संमुखी तिथिः" (p.143) | `priority = "puurvaviddha"` |
| `kRtayugAdiH` (02/03) | aparāhṇa, vyāpti | śukla yugādi → **pūrvāhṇa** ("शुक्ले पौर्वाह्णिके ज्ञेये कृष्णे चैवापराह्णिके", p.111) | kaala → पूर्वाह्णः (mention aparāhṇa as gauṇa per Kālādarśa) |
| `trEtAyugAdiH` (08/09) | sāṅgava, para | same rule → pūrvāhṇa (p.111, p.378) | kaala → पूर्वाह्णः |
| (note) yugādi identity | kṛta=vai.ś3, tretā=kā.ś9 | SK quotes Bhaviṣyottara: kṛta=kā.ś9, tretā=vai.ś3, dvāpara=māgha amā, kali=bhādra k13, and Brāhma: vai.ś3=kṛta; resolves by kalpa-bheda (p.110) | add both verses, keep current mapping, note variance |
| `dauhitra-pratipat` (07/01) | sāṅgava | SK rejects saṅgava: **aparāhṇa-vyāpinī** (p.281) | kaala → अपराह्णः |
| `zamI-pUjA` (07/10) | pradoṣa | aparājitā-pūjā & sīmollaṅghana **aparāhṇa** (p.352–354); śamī-pūjā happens on the sīmollaṅghana route | review; at least add aparāhṇa variant |
| `gOvardhana-pUjA` (08/01) | madhyāhna, para | **prātaḥ**; avoid pratipat where moon is seen (C6) (p.374) | kaala → प्रातः; add fall-back rule |
| `bali_pratipat` (08/01) | sūryodaya, para | bali-pūjā (night) and mārgapālī on **pūrvaviddhā** pratipat ("…शिवरात्रिर्बलेर्दिनम्") (p.377) | split: bali-pūjā (rātri, puurvaviddha) vs abhyaṅga (sunrise) |
| `upAGga-lalitA-vratam` (07/05) | madhyāhna | **pūrvaviddhā**, aparāhṇa karmakāla; if sandhyā-garjita → para (p.343) | priority/kaala fix |
| `dUrvASTamI` (06/08) | aparāhṇa, no shlokas | **rauhiṇa muhūrta**, pūrvaviddhā, avoid jyeṣṭhā/mūla, simha-ravi only (p.229–230) | kaala → रौहिणः; C4 |
| `mahAlakSmI-vrata-ArambhaH` (06/09) | śukla navamī | start **bhādra ś8** (prefer jyeṣṭhā-yoga) (p.236) | move to 06/08 |
| `mahAlakSmI-vrata-samApanam` (06/22) | k7 | end **k8, candrodaya-vyāpinī**, 4 doṣas (p.237–238) | move to 06/23, kaala चन्द्रोदयः |
| `mahAlakSmI-vratam` (07/23, Kṛtyasāra) | Āśvina k8 | SK's 16-day vrata ends bhādra k8 (amānta) | verify which tradition 07/23 represents; relabel if duplicate |
| `sarasvatI-visarjanam` (07 nakshatra 21) | uttarāṣāḍhā | **śravaṇa** for visarjana; uttarāṣāḍhā = bali (p.352) | move to nakshatra 22; add sarasvatI-bali at 21 |
| `mahA~kArttikI` (08 nakshatra 3) | kṛttikā | rohiṇī on kārtikī = **mahākārtikī**; kṛttikā = "mahāpuṇyā"; also guru+candra in kṛttikā (p.406) | tie to pūrṇimā (intersection), rename/split |
| `kapila-SaSThI` (06/21) | plain tithi | needs **bhauma + vyatīpāta + rohiṇī** (+ sun in hasta) (p.281) | intersection_groups (+C2) |
| `zukla-dEvI-pUjA` (03/09) | navamī | **aṣṭamī** ("शुक्लाष्टम्यां पुरा जाता शुक्लादेवी…", p.119) | move to 03/08 |
| `matsya~jayantI` (01/28) | Chaitra k13 aparāhṇa | SK: **Chaitra ś1** (preferred), ś3 (Mātsya), **Āṣāḍha ś11** (Varāha) (p.88) | add alternates / notes |
| `nRsiMha-dOlOtsavaH` (01/14) | ref p.90 | p.104; aparāhṇa-vyāpinī pūrvaviddhā (p.104–106) | fix ref, add kaala/priority |
| `vaizAkha-snAnapUrtiH` (02/30) | amāvāsyā | udyāpana on **vai. ś11 / ś12 / pūrṇimā** (p.116) | move to 02/15 (+alternates) |
| `kArttika-snAnapUrtiH` (08/30) | amāvāsyā | Āśvina ś10/ś11/15 → **kārtika pūrṇimā** (p.360, 389) | move to 08/15 |
| `mAgha-snAnapUrtiH` (11/30) | amāvāsyā | pauṣa ś11 → **māgha ś12 / 15** (p.439–440) | move to 11/15 (+11/12) |
| `ratha-saptamI` (11/07) | aruṇodaya, **para** | aruṇodaya; both days → **pūrva** (p.480) | `priority = "puurvaviddha"` |
| `durgASTamI` (07/08) | none | **udaya-aṣṭamī, never saptamī-viddhā** (even slight) unless navamī fails next sunrise (p.311) | priority paraviddha (+exception) |
| `mahAnavamI_or_sarasvatI-pUjA` (07/09) | none | **aṣṭamī-viddhā (pūrva)** for pūjā/upavāsa; bali on daśamī-viddhā (p.312) | priority puurvaviddha; add navamI-bali entry |
| `vaTa-pUrNimA_or_vaTa-sAvitrI-vratam` (03/15) | none | pūrṇimā/amā both **caturdaśī-viddhā** ("सावित्रीव्रतमन्तरेण…", p.124) | priority puurvaviddha |
| `kAlabhairavASTamI` (08/23) | pradoṣa, none | pradoṣa, **pūrvaviddhā** (p.428–429) | priority puurvaviddha |
| `rakSAbandhanam` (05/15) | "चैत्रः", puurvaviddha | **audayikī** pūrṇimā, aparāhṇa binding, **not in bhadrā** (p.167) | priority → paraviddha/udaya; C1 |
| `hOlikA-pUrNimA` (12/15) | pradoṣa, para | pradoṣa + **bhadrā-rahita** with 4-level fall-back (p.517–518) | C1 + C6 |
| `mAsazivarAtriH` (00/29) | niśītha, para | "bahu-rātri-vyāpinī; equal → pūrva" (prācīna) / same as annual (p.511–512) | review |
| `mahAzivarAtriH` (11/29) | niśītha, para | niśītha; **both days → pūrva** (Hemādri, Madanaratna) vs para (Mādhava) (p.483–485) | document dispute; keep para or add option |
| `ananta-caturdazI` (06/14) | "चैत्रः", pūrva | udaya + 3 muhūrta; pūrṇimā-yoga preferred (p.254–255) | review priority |
| `vAmana~jayantI` (06/12) | madhyāhna, pūrva | same; śravaṇa on ekādaśī is anukalpa (p.249) | OK – add shlokas only |
| `sarpa-pUjA~2` (08/05), `sarpa-pUjA~1` (02/05) | kārtika/vaiśākha ś5 | SK has Mārgaśīrṣa ś5 nāga-pūjā (dākṣiṇātya) (p.429) | verify sources; add 09/05 |
| `gO-trirAtra-vratam~1` (06/13) | bhādra ś13 | SK: Āśvina k13 near dīpotsava (p.368) | verify source of ~1 |
| `vasantanavarAtra-ArambhaH`, `zarannavarAtra-ArambhaH` | none | SK: pratipat **pradoṣa-vyāpinī**, amā-viddhā acceptable (SK's own view), vs udaya (Gauḍa) (p.292–297) | document; choose default |

---------------------------------------------------------------------------------------------------

## 5. Month-by-month catalogue

Format of each row: **id / proposed id** — status — timing — key shloka(s) (corrected) — book page — complexity.
Only the *first* or most characteristic verse is quoted in the table; [the working notes](smriti_kaustubha_notes.md) have the fuller text.

### 5.1 Chaitra (चैत्रकृत्यम्, pp.85–108)

| Item | Status | Timing | Key shloka(s) | p. | Cx |
|---|---|---|---|---|---|
| `yugAdiH` / saṃvatsarārambha | ADD-SH | 01/01 udaya; both/neither → pūrva | "चैत्रे मासि जगद्ब्रह्मा ससर्ज प्रथमेऽहनि। शुक्लपक्षे समग्रं तु तदा सूर्योदये सति॥ प्रवर्तयामास तथा कालस्य गणनामपि॥"; "वत्सरादौ वसन्तादौ बलिराज्ये तथैव च। पूर्वविद्धैव कर्तव्या प्रतिपत्सर्वदा बुधैः॥" | 85 | S |
| saṃvatsarādi tailābhyaṅga | ADD-SH (to yugAdiH) or NEW | 01/01 | "वत्सरादौ वसन्तादौ बलिराज्ये तथैव च। तैलाभ्यङ्गमकुर्वाणो नरकं प्रतिपद्यते॥" | 86 | S |
| brahma-pūjā / mahāśānti | NEW `brahma-pUjA_saMvatsarArambhE` | 01/01 | "तत्र कार्या महाशान्तिः सर्वकल्मषनाशिनी। सोत्पातप्रशमनी कलिदुःस्वप्ननाशिनी॥ तस्यामादौ तु संपूज्यो ब्रह्मा कमलसंभवः…"; damanaka: "चैत्रादौ कारयेत्पूजां मम वत्स यथाविधि। गन्धधूपार्चनादानैर्माल्यैश्च दमनोद्भवैः॥" | 86 | S |
| vatsarādhipa-pūjā / dhvaja | NEW `vatsarAdhipa-pUjA` | 01/01 | "यश्चैत्रशुक्लप्रतिपद्दिनवारो नृपो हि सः। तस्य पूजा विधातव्या पताकातोरणादिभिः॥ प्रतिगृहं ध्वजाकर्म…" | 87 | S |
| nimba-patra-prāśana + pañcāṅga-śravaṇa (lunar) | NEW `nimba-patra-prAzanam~cAndra` (existing nimba entry is solar) | 01/01 | "चैत्रे मासि महाबाहो पुण्या या प्रतिपत्परा। अस्यां वै निम्बपत्राणि प्राश्य संशृणुयात्तिथिम्॥ शकवत्सरभूपमन्त्रिणां रसधान्येश्वरमेघपतीनाम्। श्रवणात्पठनाच्च वै नृणां शुभतां यात्यशुभं सह श्रिया॥" | 87 | S |
| vidyā-vratam | NEW `vidyA-vrata-ArambhaH` | 01/01 (then every ś1 for a year) | "चैत्रशुक्लामथारभ्य सोपवासो जितेन्द्रियः। सदा प्रतिपदं प्राप्य शुक्लपक्षस्य यादव…" | 87 | S |
| **30 kalpādis (Nāgarakhaṇḍa)** | NEW family (currently only the 7 Mātsya kalpādis exist) | see list | "अथ कल्पादयो राजन्कथ्यन्ते तिथयः शुभाः। यासु श्राद्धे कृते तृप्तिः पितॄणामक्षया भवेत्…" | 87–88 | S (list needs clean scan) |
| matsya-jayantī | FIX/ADD-SH | 01/01 (pref.), 01/03, 04/11 | "मत्स्योऽभूद्धुतभुग्दिने मधुसिते"; "कृते च प्रभवे चैत्रे प्रतिपच्छुद्धपक्षगा। रेवत्यां योगविष्कम्भे…"; arghya "सत्यव्रतोपदेशाय जिह्ममीनस्वरूपधृक्। प्रलयाब्धिकृतावास गृहाणार्घ्यं नमोऽस्तु ते॥" | 88 | S |
| `vasantanavarAtra-ArambhaH` | ADD-SH | 01/01 | "शरत्काले महापूजा क्रियते या च वार्षिकी। वसन्तकाले सा प्रोक्ता कार्या सर्वैः शुभार्थिभिः॥" | 89 | S |
| chaitra gaurī-vrata (month) | ADD-SH to `caitra-mAsa-ArambhaH` | month | "वर्जयित्वा मधौ यस्तु दधिक्षीरघृतैक्षवम्…गौरी मे प्रीयतामिति। एतद्गौरीव्रतं नाम भवानीलोकदायकम्॥" | 89 | S |
| `prapAdAnArambhaH` | ADD-SH (check) | 01/01 | "प्रपेयं सर्वसामान्या भूतेभ्यः प्रतिपादिता…"; "एष धर्मघटो दत्तो ब्रह्मविष्णुशिवात्मकः…" | 89–90 | S |
| umā-śiva-agni damanaka pūjā | NEW `umA-ziva-agni-damanaka-pUjA` | 01/02 | "उमां शिवं हुताशं च द्वितीयायां तु पूजयेत्। हविष्यमन्नं नैवेद्यं देयं गन्धार्चनान्वितम्॥" | 90 | S |
| `AndOlana~tRtIyA` / rāma-dolotsava | ADD-SH (none now) | 01/03, not dvitīyā-viddhā | "मधौ शुक्लतृतीयायां जानकीरमणं प्रभुम्। राजोपचारैः सम्पूज्य मासमान्दोलयेत्कलौ॥ दोलारूढं प्रपश्यन्ति ये कृष्णं मधुमाधवे। अपराधसहस्रैस्तु मुक्तास्ते नात्र संशयः॥"; nitya: "ऊर्जे व्रतं मधौ दोलां श्रावणे तन्तुपूजनम्। चैत्रे दमनकारोपमकुर्वाणो व्रजत्यधः॥" | 91 | S |
| manvādi (Mātsya list) | ADD-SH to all `manvAdiH~*` | – | "आश्वयुक्शुक्लनवमी द्वादशी कार्तिकस्य च। तृतीया चैत्रमासस्य तथा भाद्रपदस्य च…" | 91–92 | S |
| **damanaka tithi list** | ADD-SH to all damanaka entries + NEW gaṇapati (01/04), durgā (01/09), sarvadeva (01/15) | – | "चतुर्थी गणनाथस्य दुर्गाया नवमी तथा। विष्णोस्तु नवमी पुण्या तथैव द्वादशी शुभा। त्रयोदश्यनङ्गस्यैव… भैरवस्यैकवीराया ज्ञेया भूता फलप्रदा। पूर्णिमा सर्वदेवानां श्रेष्ठा दमनकार्पणे॥"; gaṇeśa: "गणेशे कारयेत्पूजां लड्डुकादिभिरादरात्। चतुर्थ्यां विघ्ननाशाय सर्वकामसमृद्धये॥" | 92 | S |
| `lakSmI-paJcamI`, `haya-pUjA` | ADD-SH (verify) | 01/05 | "शुक्लायामथ पञ्चम्यां चैत्रे मासि शुभानना। श्रीविष्णुलोकान्मानुष्यं संप्राप्ता केशवाज्ञया…"; "उच्चैःश्रवाः पूजनीयः पञ्चम्यां चैत्रशुक्लके…" | 92–93 | S |
| chaitra nāga-pūjā | NEW `caitra-nAga-pUjA` | 01/05 | "पञ्चम्यां पूजयेन्नागाननन्ताद्यान्महोरगान्। क्षीरं सर्पिस्तु नैवेद्यं देयं सर्वसुखावहम्॥" (+ nāga-pratimā lakṣaṇa, Mātsya) | 93 | S |
| skanda-janma / skanda-pūjā | NEW `skanda-SaSThI~caitra` | 01/06 (pūrvaviddhā per Dīpikā) | "जातः स्कन्दश्च षष्ठ्यां तु शुक्लायां चैत्रनामनि। सैनापत्येऽभिषिक्तश्च देवानां ब्रह्मणा स्वयम्…सर्वासु शुक्लषष्ठीषु कार्यमेवं न संशयः॥"; 12 monthly names: षण्मुख, पार्वतीपुत्र, स्कन्द, गुह, कुमारक, कार्तिकेय, बाल, क्रौञ्चसूदन, तारकाराति, कृत्तिकासुत, वैशाख, विशाख | 93–94 | S |
| `sUryasya~damanakapUjA` | ADD-SH (verify) | 01/07 | "भास्करस्य तु सप्तम्यां पूजां दमनकादिभिः…" | 94 | S |
| `azOkASTamI` | ADD-SH | 01/08 (+punarvasu) | "अशोककलिकाश्चाष्टौ ये पिबन्ति पुनर्वसौ। चैत्रे मासि सिताष्टम्यां ते न शोकमवाप्नुयुः॥"; mantra "त्वामशोक नराभीष्ट मधुमाससमुद्भव। पिबामि शोकसंतप्तो मामशोकं सदा कुरु॥" | 94 | S |
| bhavānī-yātrā | ADD-SH to `bhavAnyutpattiH` or NEW | 01/08 | "चैत्राष्टम्यां महायात्रा भवान्याः कारयेत्सुधीः। अष्टाधिकाः प्रकर्तव्याः शतकृत्वः प्रदक्षिणाः॥" (Kāśīkhaṇḍa) | 94 | S |
| `vAjapEyaphala-snAna-yOgaH` | ADD-SH | 01/08 + punarvasu + budha | "पुनर्वसुबुधोपेता चैत्रे मासि सिताष्टमी। प्रातस्तु विधिना स्नात्वा वाजपेयफलं लभेत्॥" | 94 | – |
| `zrIrAmanavamI` | ADD-SH | 01/09 madhyāhna; vaiṣṇava vs smārta viddhā | "चैत्रे नवम्यां प्राक्पक्षे दिवा पुण्ये पुनर्वसौ। मेषे पूषणि संप्राप्ते लग्ने कर्कटकाह्वये। आविरासीत्स कलया कौसल्यायां परः पुमान्॥"; "नवमी चाष्टमीविद्धा त्याज्या विष्णुपरायणैः। उपोषणं नवम्यां च दशम्यां चैव पारणम्॥"; arghya "दशाननवधार्थाय धर्मसंस्थापनाय च…"; pāraṇa "तव प्रसादं स्वीकृत्य क्रियते पारणं मया…"; not in malamāsa | 94–101 | S |
| `dharmarAja-dazamI`, `RSINAM~damanakapUjA` | ADD-SH (verify) | 01/10, 01/11 | "धर्मराजं दशम्यां तु पूजयित्वा सुगन्धिभिः…"; "एकादश्यां ऋषेः पूजा कार्या सर्वोपहारिकी…" | 101 | S |
| `zrIkRSNadOlOtsavaH` | ADD-SH (Gāruḍa māhātmya) | 01/11 | "दोलारूढं प्रपश्यन्ति कृष्णं कलिमलापहम्। अपराधसहस्रैस्तु मुक्तास्ते घूर्णने कृते…" | 101 | S |
| `viSNu-damanakOtsavaH`, `damanakArOpaNa-dvAdazI` | ADD-SH (latter has none) | 01/12; if no dvādaśī on pāraṇa day → 13 | "द्वादश्यां चैत्रमासस्य शुक्लायां दमनोत्सवः। बौधायनादिभिः प्रोक्तः कर्तव्यः प्रतिवत्सरम्॥ पारणाहे न लभ्येत द्वादशी घटिकापि चेत्। तदा त्रयोदशी ग्राह्या पवित्रदमनार्पणे॥"; fallback "माधवे दमनारोपो मधौ न विहितो यदि। वैशाख्यां श्रावणे भाद्रे कर्तव्यं वा तदर्पणम्॥"; arpaṇa "देवदेव जगन्नाथ वाञ्छितार्थप्रदायक…इमां सांवत्सरीं पूजां भगवन्परिपूरय॥"; MBh "अहोरात्रेण द्वादश्यां चैत्रे विष्णुरिति स्मरन्। पौण्डरीकमवाप्नोति देवलोकं च गच्छति॥" | 101–104 | S |
| `madana-trayOdazI` | FIX+ADD | 01/13 pūrvaviddhā | "चैत्रशुक्लत्रयोदश्यां मदनं चम्पकात्मकम्। कृत्वा संपूज्य यत्नेन वीजयेद्व्यजनेन तु…" | 104 | S |
| `nRsiMha-dOlOtsavaH` | FIX+ADD | 01/14 aparāhṇa pūrvaviddhā | "मधौ शुक्लचतुर्दश्यां नृसिंहं जगतः प्रभुम्। राजोपचारैः संपूज्य मासमान्दोलयेत्कलौ। दक्षिणाभिमुखं देवं दोलमानं सुरेश्वरम्। संपूजितं सकृद्दृष्ट्वा सर्वपापैः प्रमुच्यते॥"; rule "मधोः श्रावणमासस्य या स्याच्छुक्लचतुर्दशी। सा रात्रिव्यापिनी ग्राह्या परा पूर्वाह्णगामिनी॥" | 104–106 | S |
| śiva-pūjotsava + `damanaka-caturdazI` | ADD-SH (none now) | 01/14 rātri | "चतुर्दश्यां तु कर्पूरकुङ्कुमागरुचन्दनैः। वस्त्रादिमणिभिः पूजा कर्तव्या महती शिवे…"; "दमनकचतुर्दशीं वक्ष्यामि…पूज्यते शंकरो रात्रौ तस्माद्दमनचतुर्दशी॥"; Varāha "चैत्रे मासि चतुर्दश्यां यः स्नायाच्छिवसंनिधौ। गङ्गायां तु विशेषेण स न प्रेतोऽभिजायते॥" | 106 | S |
| citra-vastra-dāna | NEW `caitrI-citrA-vastra-dAnam` | 01/15 + citrā | Viṣṇu-smṛti: "चैत्री चित्रायुता चेत्स्यात्तस्यां चित्रवस्त्रप्रदानेन सौभाग्यमाप्नोति" (see family §6.4) | 106 | M |
| sadāśiva damanaka (caitrī) | ADD-SH to `caitra-pUrNimA` / NEW | 01/15 | "संवत्सरकृतार्चायाः साफल्यायाखिलान्सुरान्। दमनेनार्चयेच्चैत्र्यां विशेषेण सदाशिवम्॥" | 106 | S |
| vaiśākha-snāna ārambha | NEW `vaizAkha-snAna-ArambhaH` (options 01/11, 01/15, meṣa-saṅkrānti) | – | "मधुमासस्य शुक्लायामेकादश्यामुपोषितः। पञ्चदश्यां च भो वीर मेषसंक्रमणे नरः…"; saṅkalpa "वैशाखं सकलं मासं मेषसंक्रमणे रवेः। प्रातः सनियमः स्नास्ये प्रीयतां मधुसूदनः॥" | 106–107 | M |
| avicCheda-vratam | NEW | 01/23 (then every k8 for a year) | "शृणु दाल्भ्य परं काम्यं व्रतं संततिदं नृणाम्। यदुपोष्य न विच्छेदः पुत्रपित्रोश्च जायते। कृष्णाष्टम्यां चैत्रमासे…" | 107 | S |
| vāruṇī / mahāvāruṇī / mahāmahāvāruṇī | ADD-SH (exist, NS) | 01/28 + śatabhiṣā (+śani, +śubha yoga) | "वारुणेन समायुक्ता मधौ कृष्णा त्रयोदशी। गङ्गायां यदि लभ्येत शतसूर्यग्रहैः समा॥ शनिवारसमायुक्ता सा महावारुणी मता…" | 107 | – |
| `pizAcamOcanam` | ADD-SH/verify vāra | 01/29 (+maṅgalavāra) | "चैत्रकृष्णचतुर्दश्यामङ्गारकदिनं यदि। पिशाचत्वं पुनर्न स्याद्गङ्गायां स्नानभोजनात्॥" | 108 | M |
| `vahni-vratam` | ADD-SH (none now) | 01/30 (then every amā); pūrvaviddhā | "कृष्णपक्षे पञ्चदश्यां चैत्रादारभ्य यादव। वह्निसंपूजनं कृत्वा गन्धमाल्यान्नसंपदा। तिलहोमं तथा कुर्यात्…" | 108 | S |

**30 Nāgarakhaṇḍa kalpādis (p.87–88)** – proposed ids `<name>-kalpAdiH` (the 7 Mātsya ones already exist; verify overlaps):
ch.ś1 śveta · ch.ś13 udāna[?] · ch.k1 nārasiṃha · ch.k13 gaurī · vai.ś3 nīlalohita · vai.ś14 gāruḍa · vai.k3 samāna · vai.k14 māheśvara ·
jy.ś3 mahādeva · jy.15 kūrma · jy.k3 āgneya · āṣ.k3 soma · śrā.ś5 raurava/mānava[?] · śrā.k5 mānava · bhā.ś6 prāṇādhipa · bhā.k6 tatpuruṣa ·
āś.ś7 bṛhat · āś.k7 vaikuṇṭha · kā.ś6 kandarpa · kā.k6 lakṣmī · mā.ś9 sadyaḥ · mā.k9 sāvitrī · pau.ś10 īśāna · pau.k10 mayūra ·
māgha.ś11 vyāna · māgha.k11 vārāha · phā.ś12 sārasvata · phā.k12 vairāja (+ remaining 2 from clean scan). Kaala: aparāhṇa (śrāddha).

### 5.2 Vaiśākha (वैशाखकृत्यम्, pp.108–116)

| Item | Status | Timing | Key shloka(s) | p. | Cx |
|---|---|---|---|---|---|
| `vaizAkha-mAsa-ArambhaH` | ADD-SH | month | "निश्चरेदेकभक्तेन वैशाखे यो जितेन्द्रियः। प्रातःस्नायी नरः स्त्री वा ज्ञातीनां श्रेष्ठतां व्रजेत्॥"; "तुलसी कृष्णगौराख्या तयाभ्यर्च्य मधुद्विषम्। विशेषेण तु वैशाखे नरो नारायणो भवेत्॥"; "प्रपा कार्या च वैशाखे देवे देया गलन्तिका। उपानद्व्यजनच्छत्रसूक्ष्मवासांसि चन्दनम्…" | 108–109 | S |
| jala-pātra-stha śālagrāma pūjā | NEW (month-long; also jyeṣṭha) | 02/01–02/30 | "निक्षिप्य जलपात्रे तु प्राप्ते माधवसंज्ञके। माधवं येऽर्चयिष्यन्ति देवतास्ते नरा भुवि॥" | 108 | S |
| `akSaya-tRtIyA` | ADD-SH | 02/03 | "वैशाखस्य तृतीयायां श्रीसमेतं जगद्गुरुम्। नारायणं पूजयेत पुष्पधूपविलेपनैः॥"; "तस्यां कार्यो यवैर्होमो यवैर्विष्णुं समर्चयेत्। यवान्दद्याद्द्विजातिभ्यः प्रयतः प्राशयेद्यवान्॥"; "अस्यां तिथौ क्षयमुपैति हुतं न दत्तं तेनाक्षयेति कथिता मुनिभिस्तृतीया…" | 109–110 | S |
| akṣaya-tṛtīyā + rohiṇī + budha | NEW `mahA-akSaya-tRtIyA-yOgaH` | 02/03 ∧ rohiṇī (∧ budhavāra) | "यदा स्याद्बुधसंयुक्ता (रोहिणीयुता) तदा सा सुमहाफला"; devī-P "तृतीयायां तु वैशाखे रोहिण्यृक्षे प्रपूज्य तु। उदकुम्भप्रदानेन शिवलोके महीयते॥" | 109, 112 | M |
| `candana-pUjA` | ADD-SH | 02/03 | "यः पश्यति तृतीयायां कृष्णं चन्दनभूषितम्। वैशाखस्य सिते पक्षे स यात्यच्युतमन्दिरम्॥" | 109 | S |
| yugādi śrāddha (all four) | ADD-SH | – | "द्वे शुक्ले द्वे तथा कृष्णे युगादी कवयो विदुः। शुक्ले पौर्वाह्णिके ज्ञेये कृष्णे चैवापराह्णिके॥"; "अयनद्वितये श्राद्धं विषुवद्वितये तथा। युगादिषु च सर्वासु पिण्डनिर्वपणादृते॥"; "पानीयमप्यत्र तिलैर्विमिश्रं दद्यात्पितृभ्यः प्रयतो मनुष्यः…"; adhika: both months | 110–112 | S |
| `parazurAma~jayantI~1` | ADD-SH | 02/03 pradoṣa/first yāma | "वैशाखस्य सिते पक्षे तृतीयायां पुनर्वसौ। निशायाः प्रथमे यामे रामाख्यः समभूद्धरिः। रेणुकायास्तु यो गर्भादवतीर्णो हरिः स्वयम्॥"; arghya "जमदग्निसुतो वीर क्षत्रियान्तकर प्रभो। गृहाणार्घ्यं मया दत्तं कृपया परमेश्वर॥" | 112 | S |
| `gaGgA-saptamI` | ADD-SH | 02/07 | "वैशाखशुक्लसप्तम्यां जह्नुना जाह्नवी पुरा। क्रोधात्पीता पुनस्त्यक्ता कर्णरन्ध्रात्तु दक्षिणात्। तां तत्र पूजयेद्देवीं गगनाङ्गणमेखलाम्॥" | 112 | S |
| `zarkarA-saptamI` | ADD-SH (verify) | 02/07 | "अमृतं पिबतो वक्त्रात्सूर्यस्यामृतबिन्दवः…शर्करासप्तमी चैषा वाजिमेधफलप्रदा॥" | 112–113 | S |
| aparājitā/devī (āmra-rasa snāna) | NEW `aparAjitA-pUjA~vaizAkha` | 02/08 (pāraṇa 9) | "सहकारफलैः स्नानं वैशाखे ह्यष्टमीदिने। आत्मनो देवतां स्नाप्य मांसीवालकवारिभिः…"; "देव्याः पूजां प्रकुर्वीत केतक्या चम्पकेन च…" | 113 | S |
| caṇḍikā navamī (both pakṣas) | NEW | 02/09, 02/24 | "वैशाखे मासि राजेन्द्र नवम्यां पक्षयोर्द्वयोः। उपवासपरो भक्त्या पूजयानस्तु चण्डिकाम्…" (see family §6.3) | 113 | S |
| `madhusUdana-pUjA` | ADD-SH (verify) | 02/12 | "वैशाखमासे द्वादश्यां पूजयेन्मधुसूदनम्। अग्निष्टोममवाप्नोति सोमलोकं च गच्छति॥" | 114 | S |
| vaiśākha ś12 "vyatīpāta" graha-yoga | SKIP (C8) | 02/12 ∧ hasta ∧ sun meṣa ∧ guru+kuja siṃha | "पञ्चाननस्थौ गुरुभूमिपुत्रौ मेषे रविः स्याद्यदि शुक्लपक्षे। पाशाभिधाना करभेण युक्ता तिथिर्व्यतीपात इतीह योगः॥" | 114 | H |
| kāmadeva-vratam | NEW `kAmadeva-vrata-ArambhaH` | 02/13 (then every ś13) | "शुक्लपक्षे महाराज त्रयोदश्यामुपोषितः। पूजयेत्कामदेवं तु वैशाखात्प्रभृति प्रभो॥" | 114 | S |
| `nRsiMha~jayantI` | ADD-SH | 02/14 sāyaṃ-sandhyā; svāti-yoga praśasta | "वैशाखस्य सिते पक्षे चतुर्दश्यां महातिथौ। जयन्ती तत्र कर्तव्या नृसिंहस्य द्विजोत्तमैः॥"; "भूतायां शुक्लपक्षे च वैशाखे तु निशामुखे। वायुभं यदि लभ्येत सोपोष्या सा महाफला॥"; arghya "हिरण्याक्षवधार्थाय भूभारोत्तारणाय च…" | 114–115 | S |
| vaiśākhī tila/kṛṣṇājina/udakumbha dāna | NEW `vaizAkhI-tila-dAnam` (+viśākhā yoga) | 02/15 | "वैशाख्यां पौर्णमास्यां च सृष्टाः कमलयोनिना। तिलाः कृष्णाश्च गौराश्च तृप्तये सर्वदेहिनाम्…"; mantra "तिला वै सोमदैवत्याः सुरैः सृष्टास्तु गोसवे। स्वर्गप्रदाः स्वतन्त्राश्च ते मां रक्षन्तु नित्यशः॥"; "यस्तु कृष्णाजिनं दद्यात्सखुरं शृङ्गसंयुतम्…वैशाख्यां पौर्णमास्यां तु विशाखासु विशेषतः…"; "सान्नमुदकुम्भं च वैशाख्यां च विशेषतः। निर्दिश्य धर्मराजाय गोदानफलमाप्नुयात्॥" | 115–116 | S/M |
| vaiśākha-snāna udyāpana | FIX `vaizAkha-snAnapUrtiH` | 02/11 / 02/12 / **02/15** | "मासमेवं बहिः स्नात्वा नद्यादौ विमले जले। एकादश्यां वा द्वादश्यां पौर्णमास्यामथापि वा। उपोष्य नियतो भूत्वा कुर्यादुद्यापनं बुधः॥" | 116 | S |
| jalastha-jagadīśvara mahotsava | NEW | 02/15 → till jy.ś11 | "वैशाखे पूर्णमास्यां वै जलस्थं जगदीश्वरम्। पूजयेद्वैष्णवो भक्त्या कृत्वोत्साहं मुदान्वितः…" | 116–117 | S |

### 5.3 Jyeṣṭha (ज्येष्ठकृत्यम्, pp.117–137)

| Item | Status | Timing | Key shloka(s) | p. | Cx |
|---|---|---|---|---|---|
| `jyaiShTha-mAsa-ArambhaH` | ADD-SH | month | "पिष्टेन कञ्जं कृत्वा ज्येष्ठे मासि सवेदिकम्…"; "उदकुम्भाम्बु धेनुं च तालवृन्तं सचन्दनम्। त्रिविक्रमस्य प्रीत्यर्थं दातव्यं ज्येष्ठमासि वा॥" | 117 | S |
| `karavIra-vratam` | ADD-SH | 03/01 | "ज्येष्ठे मासि सिते पक्षे प्रथमेऽह्नि दिनोदये। देवोद्यानभवं हृद्यं करवीरं समर्चयेत्॥"; "करवीर विषावास नमस्ते भानुवल्लभ। मौलिमण्डन दुर्गादिदेवानां सततं प्रिय॥" | 117 | S |
| `rambhA~tRtIyA` | ADD-SH | 03/03 pūrvaviddhā (OK) | "ज्येष्ठशुक्लतृतीयायां स्नाता नियमतत्परा…"; "वेदेषु सर्वशास्त्रेषु दिवि भूमौ रसातले…त्वं शक्तिस्त्वं स्वधा स्वाहा त्वं सावित्री सरस्वती। पतिं देहि सुतान्देहि गृहं देहि नमोऽस्तु ते॥" | 117–119 | S |
| `umA-avatAraH` | ADD-SH | 03/04 | "ज्येष्ठशुक्लचतुर्थ्यां तु जाता पूर्वमुमा सती। तस्मात्सा तत्र संपूज्या स्त्रीभिः सौभाग्यवृद्धये॥" | 119 | S |
| `zukla-dEvI-pUjA` | FIX (→03/08) + ADD | 03/08 | "शुक्लाष्टम्यां पुरा जाता शुक्लादेवी महाशनिः। वधाय दानवेन्द्राणां शुक्लपक्षेऽथ तां यजेत्॥" | 119 | S |
| `brahmANI-pUjA` | ADD-SH (none now) | 03/09 | "उपवासपरो भक्त्या नवम्यां पूजयेदुमाम्। ब्रह्माणीमिति वै नाम्ना श्वेतरूपेण रूपिणीम्॥" | 119 | S |
| `dazaharA…` | ADD-SH | 03/10 pūrvāhṇa-vyāpinī (not yoga-count) | "दशम्यां शुक्लपक्षे च ज्येष्ठे मासि कुजे दिने। गङ्गावतीर्णा हस्तर्क्षे सर्वपापहरा स्मृता॥"; "ज्येष्ठे मासि सिते पक्षे दशम्यां बुधहस्तयोः। व्यतीपाते गरानन्दे कन्याचन्द्रे वृषे रवौ॥"; "ज्येष्ठस्य शुक्लदशमी संवत्सरमुखी स्मृता…यां कांचित्सरितं प्राप्य दद्याद्दर्भतिलोदकम्…"; Daśaharā stotra (36 ślokas) | 119–122 | S |
| daśa-yoga variant | NEW `mahA-dazaharA-yOgaH` | 03/10 ∧ hasta ∧ (budha ∨ kuja) (∧ vyatīpāta) | as above | 119 | M |
| `pANDava-nirjalA-EkAdazI` | ADD-SH (mantra only; ekādaśī otherwise skipped) | 03/11 | "देवदेव हृषीकेश संसारार्णवतारक। उदकुम्भप्रदानेन यास्यामि परमां गतिम्॥" | 122 | S |
| `gavAmayana-dvAdazI` | verify | 03/12 | "अहोरात्रेण द्वादश्यां ज्येष्ठे मासि त्रिविक्रमम् (पूजयेत्)। गवामयनमाप्नोति अप्सरोभिश्च मोदते॥" | 123 | S |
| rudra-vrata (pañcatapas) | NEW (LOW) | 03/08, 03/14 | "ज्येष्ठे पञ्चतपाः सायं हेमधेनुप्रदो दिवम्। यात्यष्टमीचतुर्दश्यो रुद्रव्रतमिदं स्मृतम्॥" | 123 | S |
| jyeṣṭhī tila-dāna; jyeṣṭhā chatropānad-dāna | NEW (family §6.4) | 03/15; 03/15∧jyeṣṭhā | "ज्येष्ठे मासि तिलान्दद्यात्पूर्णमास्यां विशेषतः। अश्वमेधस्य यत्पुण्यं तत्प्राप्नोति न संशयः॥"; "ज्येष्ठी ज्येष्ठायुता चेत्स्यात्तस्यां छत्रोपानद्दानेन नराधिपत्यमाप्नोति" | 123 | S/M |
| bilva-trirātri-vratam | NEW | 03/13–15 (jyeṣṭhā ∧ kuja preferred); year-long | "ज्येष्ठे मासि तु संप्राप्ते पौर्णमास्यां द्विजोत्तम। ज्येष्ठाकुजदिने कुर्यात्सिद्धार्थैः स्नानमुत्तमम्…"; "श्रीनिकेत नमस्तुभ्यं शिवप्रिय नमोऽस्तु ते। अवैधव्यं च मे देहि श्रियं जन्मनि जन्मनि॥"; arghya "उमापते पशुपते त्रैलोक्याधिपते प्रभो। गृहाणार्घ्यमिदं देव गौर्या सह महेश्वर॥" | 123–124 | S/M |
| `vaTa-pUrNimA…` | FIX+ADD | 03/15 (caturdaśī-viddhā); **also amā variant 03/30**; trirātra from 03/13; Parāśara 14th-day variant | "अमायां च तथा ज्येष्ठे वटमूले महासती। त्रिरात्रोपोषिता नारी विधिनानेन पूजयेत्…"; "ज्येष्ठशुक्लचतुर्दश्यां सावित्रीमर्चयन्ति याः। वटमूले सोपवासा न ता वैधव्यमाप्नुयुः॥"; "वट सिञ्चामि ते मूलं सलिलैरमृतोपमैः…"; "नमोऽव्यक्तस्वरूपाय महाप्रणवरूपिणे। महदासोपविष्टाय न्यग्रोधाय नमोऽस्तु ते॥"; arghya "ओंकारपूर्वके देवि सर्वदुःखनिवारिणि। वेदमातर्नमस्तुभ्यमवैधव्यं प्रयच्छ मे॥"; yama "त्वं कर्मसाक्षी लोकानां शुभाशुभविवेचकः। वैवस्वत गृहाणार्घ्यं धर्मराज नमोऽस्तु ते॥"; dāna "सावित्रीयं मया दत्ता सहिरण्या महासती। ब्रह्मणः प्रीणनार्थाय ब्राह्मण प्रतिगृह्यताम्॥"; monthly vaṭa-secana with 12 names of Yama | 124–137 | S |
| NEW `vaTa-sAvitrI-vratam~amAvAsyA` | NEW | 03/30 caturdaśī-viddhā | as above | 124–125 | S |
| mahājyeṣṭhī | NEW-CODE (C2) | 03/15 ∧ guru & candra in jyeṣṭhā ∧ sun in rohiṇī | "ऐन्द्रे गुरुः शशी चैव प्राजापत्ये रविस्तथा। पौर्णिमा ज्येष्ठमासस्य महाज्येष्ठी प्रकीर्तिता॥" | 137 | H |

### 5.4 Āṣāḍha (आषाढकृत्यम्, pp.137–148)

| Item | Status | Timing | Key shloka(s) | p. | Cx |
|---|---|---|---|---|---|
| `ASADha-mAsa-ArambhaH` | ADD-SH | month | "आषाढमेकभक्तेन स्थित्वा मासमतन्द्रितः। बहुधान्यो बहुधनो बहुपुत्रश्च जायते॥"; "उपानद्युगलं छत्रं लवणामलकानि च। आषाढे वामनप्रीत्यै दातव्यानि तु भक्तितः॥" | 137 | S |
| `jagannAtha-ratha-yAtrA` | ADD-SH (none now); puṣya-yoga preferred | 04/02 | "आषाढस्य सिते पक्षे द्वितीया पुष्यसंयुता। तस्यां रथे समारोप्य रामं मां भद्रया सह। यात्रोत्सवं प्रवर्त्याथ प्रीणयेच्च द्विजान्बहून्॥ ऋक्षाभावे तिथौ कार्या यात्रा संप्रीतये मम॥" | 137 | S (M for puṣya pref.) |
| kumāra-ṣaṣṭhī (Āṣāḍha) | NEW `kumAra-SaSThI~ASADha` | 04/06 (upavāsa on 5th) | "आषाढशुक्लषष्ठी तु तिथिः कौमारिका स्मृता। कुमारमर्चयेत्तत्र पूर्वत्रोपोष्य वै दिनम्॥" | 138 | S |
| `vaivasvata-saptamI`, `mahiSaghnI-pUjA`, `aindrI-durgA-pUjA` | verify (SK p.138 already); add **04/24** for aindrī (both pakṣas) | 04/07, 04/08, 04/09 & 04/24 | "आषाढशुक्लसप्तम्यां विवस्वान्नाम भास्करः…"; "…नवम्यां पक्षयोर्द्वयोः…दुर्गामैन्द्रीनाम्नीं तु नामतः…" | 138 | S |
| `viSNu-zayanOtsavaH` | ADD-SH (none now) | 04/11 (and dvādaśī variant) | "एकादश्यां तु शुक्लायामाषाढे भगवान्हरिः। भुजगशयने शेते यदा क्षीरार्णवे स्वयम्…"; "सुप्ते त्वयि जगन्नाथे जगत्सुप्तं भवेदिदम्। विबुद्धे त्वयि बुध्येत तत्सर्वं सचराचरम्॥"; pāraṇa "आभाकासितपक्षेषु मैत्रश्रवणरेवती। सङ्गवे नहि भोक्तव्यं द्वादश द्वादशीर्हरेत्॥" | 138–139 | S (nakṣatra-pāda variant H) |
| `cAturmAsyavrata-ArambhaH` & shāka/dadhi/payo/dvidala | ADD-SH (verify each) | 04/11–12 … | "श्वेतद्वीपे भोगिनाथे योगिनाथे स्थिते त्वयि। चातुर्मास्यव्रतेऽनुज्ञां देहि लक्ष्मीपते मम…"; "श्रावणे वर्जयेच्छाकं दधि भाद्रपदे तथा। दुग्धमाश्वयुजे मासि कार्तिके द्विदलं त्यजेत्॥"; kāmya niyamas (Bhaviṣya); haviṣya list | 139–142 | S |
| `vAsudEva-dvAdazI` / vāmana-pūjā | ADD-SH | 04/12 | "आषाढे मासि द्वादश्यां वामनेति च पूजयेत्। नरमेधमवाप्नोति पुण्यं च लभते महत्॥" | 143 | S |
| `pavitra-caturdazI` / śiva-pūjā | ADD-SH | 04/14 | "आषाढे मासि भूतायां शिवं संपूज्य मानवः। सर्वपापविनिर्मुक्तः सर्वसंपदमाप्नुयात्॥" | 143 | S |
| āṣāḍhī anna-dāna (+pūrvāṣāḍhā) | NEW (family §6.4) | 04/15 ∧ pūrvāṣāḍhā | "आषाढ्यामाषाढायुतायामन्नपानादिदानेन तदेवाक्षयमवाप्नोति" | 143 | M |
| `ziva-zayanOtsavaH` | FIX+ADD | 04/15 pūrvaviddhā | "पौर्णमास्यामुमानाथः स्वपते चर्मसंस्तरे। वैयाघ्रे च जटाभारं समुद्ग्रथ्याहिवर्मणा॥" | 143 | S |
| śiva-pavitrāropaṇa | NEW `ziva-pavitrArOpaNam` | 04/15 (alt. śrāvaṇa/bhādra k8, k14; adhivāsa on 7/13; not in adhika; fallback kanyā-ravi, never tulā) | "पूर्णमास्यां तथाषाढ्यां शिवं संपूज्य यत्नतः। उपवीतं शिवे दद्याच्छिवभक्तांश्च भोजयेत्…" | 143–144 | M |
| `guru-pUrNimA_or_vyAsa-pUjA`, `yaticAturmAsyavrata-ArambhaH` | ADD-SH; udaya 3-muhūrta; fallback dvādaśī | 04/15 | Medhātithi "आषाढ्यां पौर्णमास्यां च कारयेद्वपनं यतिः…"; saṅkalpa "माधवश्चतुरो मासान्सर्वभूतहिताय वै। निद्रां यास्यति शेषाङ्के लक्ष्म्या सह जगत्पतिः…"; mṛttikā "येनोद्धृतासि देवि त्वं क्रोडरूपेण दंष्ट्रया। त्वया सह स मां पातु केशवो धरणीधरः॥" | 144–146 | S |
| `mRgazIrSa-vratam` | ADD-SH (none now) | 04/16 | "श्रावणे कृष्णपक्षे तु शंकरः प्रथमेऽहनि। त्रिपर्वणा त्रिशल्येन शरेण त्रिमुखेन तु। मुखानि त्रीणि चिच्छेद यज्ञस्य मृगरूपिणः…" | 146 | S |
| `azUnyazayana-vratam~*` | ADD-SH; rule: candrodaya-vyāpinī, both/neither → para | 04/17 … | "श्रीवत्सधारिन् श्रीकान्त श्रीवास श्रीपतेऽव्यय। गार्हस्थ्यं मा प्रणाशं मे यातु धर्मार्थकामदम्॥"; arghya "गगनाङ्गणसंदीप क्षीराब्धिमथनोद्भव। भाभासितदिगाभोग रमानुज नमोऽस्तु ते॥" | 146–148 | S |

### 5.5 Śrāvaṇa (श्रावणकृत्यम्, pp.148–200)

| Item | Status | Timing | Key shloka(s) | p. | Cx |
|---|---|---|---|---|---|
| `zrAvaNa-mAsa-ArambhaH` | ADD-SH | month | ekabhakta (MBh); "घृतं क्षीरं ललामांश्च[?] घृतधेनुफलानि च। श्रावणे श्रीधरप्रीत्यै दातव्यानि विपश्चिता॥" | 148 | S |
| **pavitrāropaṇa tithi-devatās** | NEW family (15) + `pArvatI~pavitrArOpaNam` ADD-SH | 05/01…05/15 | "प्रतिपद्धनदस्योक्ता द्वितीया च श्रियो मता। तृतीया पार्वतीदेव्याश्चतुर्थी विघ्नहारिणः। पञ्चमी शशिनः प्रोक्ता षष्ठी प्रोक्ता गुहस्य तु। सप्तमी भास्करस्योक्ता दुर्गायाश्चाष्टमी मता। मातॄणां नवमी प्रोक्ता धर्मस्य दशमी स्मृता। एकादशी मुनीनां तु द्वादशी चक्रपाणिनः। त्रयोदशी त्वनङ्गस्य शिवस्योक्ता चतुर्दशी। पूर्णमासी सुरश्रेष्ठ पितॄणां कथिता तिथिः॥" | 148–149 | S |
| śrāvaṇa somavāra / bhaumavāra | NEW `zrAvaNa-sOmavAra-vratam`, `zrAvaNa-bhaumavAra-gaurI-pUjA` | month 5 ∧ vāra | "तस्य केदारनाथस्य श्रावणे सोमवासरे। पूजा कार्या विशेषेण साधनैर्विविधैः शुभैः। सोमवारव्रतं कार्यं प्रयत्नेन यथाविधि। शक्तेनोपोषणं कार्यमथवा निशि भोजनम्॥" | 149 | S (vaara) |
| `nAga-paJcamI` | FIX (para) + ADD | 05/05 | "पञ्चमी नागपूजायां कार्या षष्ठीसमन्विता। तस्यां तु तुषिता नागा इतरासु चतुर्थिकाः॥"; "श्रावणे मासि पञ्चम्यां शुक्लपक्षे नराधिप। द्वारस्योभयतो लेख्या गोमयेन विषोल्बणाः…" | 149 | S |
| `kaumArI-pUjA` + `caNDikA-pUjA` | ADD-SH (none now) | 05/09, 05/24 | "श्रावणे मासि राजेन्द्र यः कुर्यान्नक्तभोजनम्…नवम्यां पक्षयोर्द्वयोः। कौमारीमिति वै नाम्ना चण्डिकामर्चयेत्सदा…" | 149, 200 | S |
| viṣṇu-pavitrāropaṇa | ADD-SH to `dAmOdara-dvAdazI` or NEW | 05/12; devī-pavitra 05/08 or 05/14 (adhivāsa 7/13) | (Viṣṇurahasya via Hemādri; see p.151–153) | 151–153 | S |
| `hayagrIva~jayantI` | ADD-SH | 05/15 ∧ śravaṇa | "श्रावण्यां श्रवणे चैव पूर्वं हयशिरा हरिः। जगाद सामवेदं तु सर्वकिल्बिषनाशनम्…" | 153 | S |
| **upākarma** (all 7 entries; no shlokas today) | ADD-SH + code audit | – | Gobhila "पर्वण्यौदयिके कुर्युः श्रावणीं तैत्तिरीयकाः। बह्वृचाः श्रवणे कुर्युर्हस्ते वै सामवेदिनः॥"; "धनिष्ठाप्रतिपद्युक्तं त्वाष्ट्रऋक्षसमन्वितम्। श्रावणं कर्म कुर्वन्ति ऋग्यजुःसामपाठकाः॥"; "उदये सङ्गवस्पर्शे श्रुतौ पर्वणि चार्कभे। कुर्युर्नभस्युपाकर्म ऋग्यजुःसामगाः क्रमात्॥"; "श्रावणी पौर्णमासी तु सङ्गवात्परतो यदि। तदैवौदयिकी ग्राह्या नान्यदौदयिकी भवेत्॥"; Gārgya "अर्धरात्रात्परस्ताच्चेत्संक्रान्तिर्ग्रहणं तथा। उपाकर्म न कुर्वीत परतश्चेन्न दोषकृत्॥"; sāma: "वेदोपाकरणे प्राप्ते कुलीरे संस्थिते रवौ। उपाकर्म न कर्तव्यं कर्तव्यं सिंहयुक्तके॥"; first upākarma not in mauḍhya/adhimāsa: "गुरुभार्गवयोर्मौढ्ये बाल्ये वा वार्धकेऽपि वा। तथाधिमाससंसर्पमलमासादिषु द्विज। प्रथमोपाकृतिर्न स्यात्…"; nitya: "प्रत्यब्दं यदुपाकर्म सोत्सर्गं विधिवद्द्विजैः…" | 153–160 | S (verify code for saṅgava/ardharātra dūṣaṇa) |
| atharva-veda upākarma | NEW | śrāvaṇī or prauṣṭhapadī (Kauśika) | "श्रावण्यां प्रौष्ठपद्यां वोपाकृत्य अर्धपञ्चमासानधीयीरन्…" | 153 | M |
| utsarjana | ADD-SH to `taittirIya-utsarga*`; NEW `RgvEda-utsarjanam` (māghī / madhyamāṣṭakā), `kAtIya-utsarjanam` (pauṣa rohiṇī) | – | Āśvalāyana "मध्यमाष्टकायामेताभ्यो देवताभ्योऽनेन हुत्वा…"; Reṇukārikā "पौषमासस्य रोहिण्यां कृष्णाष्टम्यामथापि वा। माघस्याद्यतिथौ तत्र पूर्वाह्णे फाल्गुनस्य वा॥"; Āpastamba "तैष्यां पौर्णमास्यां रोहिण्यां वा विरमेत्" | 164–166 | M |
| `rakSAbandhanam` | FIX+ADD (C1) | 05/15 audayikī, aparāhṇa, no bhadrā | "संप्राप्ते श्रवणस्यान्ते पौर्णमास्यां दिनोदये। स्नानं कुर्वीत मतिमान्श्रुतिस्मृतिविधानतः…"; "येन बद्धो बली राजा दानवेन्द्रो महाबलः। तेन त्वामपि बध्नामि रक्षे मा चल मा चल॥"; "भद्रायां द्वे न कर्तव्ये श्रावणी फाल्गुनी तथा। श्रावणी नृपतिं हन्ति ग्रामं दहति फाल्गुनी॥" | 167 | H |
| śravaṇākarma (Āśvalāyana) | NEW `zravaNAkarma` (gRhya/Ashvalayana) | 05/15 astamaya; both/neither → para | Āśv. "श्रावण्यां पौर्णमास्यां श्रवणाकर्म… अस्तमिते स्थालीपाकं श्रपयित्वा"; Reṇukārikā "…आवृत्तिः सतां मता" | 167–170 | M |
| `sarpa-bali-prArambhaH` | ADD-SH (Āśvalāyana variant) | 05/15 → mārga 14/15 | "ये सर्पाः पार्थिवा ये अन्तरिक्ष्या ये दिव्या ये दिश्यास्तेभ्य इमं बलिमाहार्षम्…" | 170–171 | S |
| `bahulA~caturthI` / saṅkaṣṭa | ADD-SH (none now) + ADD to all `*-saGkaTahara-caturthI-vratam` | 05/19 candrodaya | "श्रावणे बहुले पक्षे चतुर्थ्यां तु विधूदये। गणेशं पूजयित्वा च चन्द्रायार्घ्यं च दीयते॥"; "निराहारोऽस्मि देवेश यावच्चन्द्रोदयो भवेत्। भोक्ष्यामि पूजयित्वाहं संकष्टात्तारयस्व माम्॥"; arghya "क्षीरसागरसंभूत सुधारूप निशाकर। गृहाणार्घ्यं मया दत्तं गणेश प्रीतिवर्धन॥"; udyāpana on śrāvaṇa k4 | 171–174 | S |
| `zrIkRSNajanmASTamI` | ADD-SH + C3/C5 | 05/23 niśītha | "श्रावणे बहुले पक्षे कृष्णजन्माष्टमीव्रतम्। न करोति नरो यस्तु भवति क्रूरराक्षसः॥"; "अष्टमी रोहिणीयुक्ता निश्यर्धे दृश्यते यदि। मुख्यकालः स विज्ञेयस्तत्र जातो हरिः स्वयम्॥"; "मुहूर्तेनापि संयुक्ता संपूर्णा साष्टमी भवेत्…"; "दिवा वा यदि वा रात्रौ नास्ति चेद्रोहिणी कला। रात्रियुक्तां प्रकुर्वीत विशेषेणेन्दुसंयुताम्॥"; saṅkalpa "वासुदेवं समुद्दिश्य सर्वपापप्रशान्तये। उपवासं करिष्यामि कृष्णाष्टम्यां नभस्यहम्॥"; arghya "जातः कंसवधार्थाय भूभारोत्तारणाय च…"; candra "ज्योत्स्नायाः पतये तुभ्यं ज्योतिषां पतये नमः…"; vaiṣṇava: "सर्वथा सप्तमीयुक्ता संत्याज्या सर्ववैष्णवैः…" | 177–195 | M/H |
| **jayantī-vratam** (distinct from janmāṣṭamī) | NEW-CODE | 05/23 ∧ rohiṇī; else 06/23 ∧ rohiṇī | "कृष्णाष्टम्यां भवेद्यत्र कलैका रोहिणी यदि। जयन्ती नाम सा प्रोक्ता उपोष्यैव प्रयत्नतः॥"; "श्रावणे वा नभस्ये वा रोहिणीसहिताष्टमी। यदा कृष्णा नरैर्लब्धा सा जयन्तीति कीर्तिता। श्रावणे न भवेद्योगो नभस्ये तु भवेद्ध्रुवम्॥"; budha-yoga "उदये चाष्टमी किंचिन्नवमी सकला यदि। भवेत्तु बुधसंयुक्ता प्राजापत्यर्क्षसंयुता। अपि वर्षशतेनापि लभ्यते यदि वा न वा॥" | 181–195 | H |
| janmāṣṭamī-pāraṇa | NEW `janmASTamI-pAraNam` | tithi/nakṣatra-anta rules | "जन्माष्टमी रोहिणी च शिवरात्रिस्तथैव च। पूर्वविद्धैव कर्तव्या तिथिभान्ते च पारणम्॥"; "तिथ्यृक्षयोर्यदा छेदो नक्षत्रान्तमथापि वा। अर्धरात्रेऽपि वा कुर्यात्पारणं त्वपरेऽहनि॥" | 193–194 | H |
| nandotsava | NEW `nandOtsavaH` | 05/24 | "गोपाः परस्परं हृष्टा दधिक्षीरघृताम्बुभिः। आसिञ्चन्तो विलिम्पन्तो नवनीतैश्च चिक्षिपुः॥" | 193 | S |
| kuśa-grahaṇī amāvāsyā (lunar) | NEW `kuzagrahaNI-amAvAsyA` (+ADD to solar `darbha-saGgrahaH`) | 05/30 | "नभोमासस्य दर्शे तु शुचिर्दर्भान्समाहरेत्। अयातयामास्ते दर्भा विनियोज्याः पुनः पुनः॥"; "कुशाः काशा यवा दूर्वा उशीराश्च सकुन्दकाः। गोधूमा व्रीहयो मुञ्जा दश दर्भाः सबल्वजाः॥"; "विरिञ्चिना सहोत्पन्न परमेष्ठिनिसर्गज। नुद सर्वाणि पापानि दर्भ स्वस्तिकरो भव॥" | 200 | S |

### 5.6 Bhādrapada (भाद्रपदकृत्यम्, pp.201–286)

| Item | Status | Timing | Key shloka(s) | p. | Cx |
|---|---|---|---|---|---|
| `bhAdrapada-mAsa-ArambhaH` | ADD-SH | month | "प्रोष्ठपद्यां तु यो मासमेकाहारो भवेन्नरः। धनाढ्यारोग्यमतुलं लभते नात्र संशयः॥"; "मासि भाद्रपदे दद्यात्पायसं मधुसर्पिषा। हृषीकेशप्रीणनार्थं लवणं सगुडोदनम्॥" | 201 | S |
| mahattama-vratam | NEW | 06/01 pūrvaviddhā | "मासि भाद्रपदे शुक्ले पक्षे च प्रतिपत्तिथौ। नैवेद्यं तु पचेन्मौनी षोडश त्रिगुणानि च…"; "प्रसीद देवदेवेश चराचरजगद्गुरो। वृषध्वज महादेव त्रिनेत्राय नमो नमः॥" | 201 | S |
| kāñcanī-gaurī | ADD-SH to `vipattAra-gaurI-vratam`? or NEW | 06/03 | "गुडापूपास्तु दातव्या मासि भाद्रपदे तथा। तृतीया शुक्लपक्षस्य सर्वपापहरा स्मृता॥" | 201 | S |
| `haritAlikA-vratam` | ADD-SH (para OK) | 06/03 | "हरेर्नाम्नि समुत्पन्ने हरितालि हरिप्रिये। सर्वदा सस्यमूर्तिस्थे प्रणतार्तिहरे नमः॥"; "चतुर्थीसहिता या तु सा तृतीया शुभप्रदा। अवैधव्यकरी स्त्रीणां पुत्रपौत्रफलप्रदा…"; "मन्दारमालाकुलितालकायै कपालमालाङ्कितशेखराय…" | 201–209 | S |
| `zrIvinAyaka-caturthI` | ADD-SH | 06/04 madhyāhna (pūrva OK) | "शिवा शान्ता सुखा राजंश्चतुर्थी त्रिविधा स्मृता। मासि भाद्रपदे शुक्ला शिवलोके प्रपूजिता॥"; "एकदन्तं शूर्पकर्णं गजवक्त्रं चतुर्भुजम्। पाशाङ्कुशधरं देवं ध्यायेत्सिद्धिविनायकम्॥"; "विनायक नमस्तुभ्यं सततं मोदकप्रिय। अविघ्नं कुरु मे देव सर्वकार्येषु सर्वदा॥"; 21 patra + 10 dūrvā names | 210–215 | S |
| mahā-caturthī | NEW `mahA-caturthI~bhAdrapada` | 06/04 ∧ (bhauma ∨ ravi) | "भाद्रशुक्लचतुर्थी या भौमेनार्केण वा युता। महती सात्र विघ्नेशमर्चित्वेष्टं लभेन्नरः॥" | 210 | S (vaara) |
| `bhAdrapada-candra-darzanam` | ADD-SH | 06/04 night | "सिंहादित्ये शुक्लपक्षे चतुर्थ्यां चन्द्रदर्शनम्। मिथ्याभिदूषणं कुर्यात्तस्मात्पश्येन्न तं तदा॥"; "सिंहः प्रसेनमवधीत्सिंहो जाम्बवता हतः। सुकुमारक मा रोदीस्तव ह्येष स्यमन्तकः॥" | 215–216 | – |
| `RSi-paJcamI-vratam` | ADD-SH; note viddhā dispute | 06/05 madhyāhna | "नभस्ये शुक्लपक्षे तु यदा भवति पञ्चमी। नद्यादिके तदा स्नात्वा…"; "आयुर्बलं यशो वर्चः प्रजाः पशुवसूनि च। ब्रह्मप्रज्ञां च मेधां च त्वं नो धेहि वनस्पते॥"; arghya "कश्यपोऽत्रिर्भरद्वाजो विश्वामित्रोऽथ गौतमः। जमदग्निर्वसिष्ठश्च सप्तैते ऋषयः स्मृताः…" | 216–220 | S |
| skanda-darśana ṣaṣṭhī | NEW | 06/06 | "येयं भाद्रपदे मासि षष्ठी स्याद्भरतर्षभ। इयं पापहरा पुण्या शिवा शान्ता शुभा नृप…तस्यां पश्यन्ति गाङ्गेयं दक्षिणापथमाश्रितम्…" | 220–221 | S |
| **campā-ṣaṣṭhī (bhādra)** | NEW | 06/06 ∧ vaidhṛti ∧ viśākhā ∧ bhauma | "षष्ठी भाद्रपदे शुक्ला वैधृतेन समन्विता। विशाखाभौमयोगेन सा चम्पेतीह विश्रुता॥"; "निराहारोऽद्य देवेश त्वद्भक्तस्त्वत्परायणः। पूजयिष्याम्यहं भक्त्या शरणं भव भास्कर॥" | 221–222 | M |
| `sUrya-SaSThI` | ADD-SH | 06/06 | "शुक्ले भाद्रपदे षष्ठ्यां स्नानं भास्करपूजनम्। प्राशनं पञ्चगव्यस्य अश्वमेधफलप्रदम्॥" | 222 | S |
| `amuktAbharaNa-saptamI` | ADD-SH (none now) | 06/07 madhyāhna, para (OK) | "एह्येहि भगवन्देव सर्वपापप्रणाशन। तव पूजां करिष्यामि संनिधौ भव शंकर॥"; "नमस्ते भूतनाथाय नमस्ते शशिशेखर…" | 222–227 | S |
| `dUrvASTamI` | FIX (C4) + ADD | 06/08 rauhiṇa, pūrva, ¬jyeṣṭhā/mūla, siṃha-ravi | "ब्रह्मन्भाद्रपदे मासि शुक्लाष्टम्यामुपोषितः। पूजयेच्छंकरं भक्त्या…"; "त्वं दूर्वेऽमृतजन्मासि वन्दितासि सुरासुरैः। सौभाग्यं सन्ततिं देहि सर्वकार्यकरी भव॥ यथा शाखाप्रशाखाभिर्विस्तृतासि महीतले। तथा ममापि सन्तानं देहि त्वमजरामरम्॥"; "मुहूर्ते रौहिणेऽष्टम्यां पूर्वा वा यदि वा परा। दूर्वाष्टमी तु सा ज्ञेया ज्येष्ठामूलं विवर्जयेत्॥"; "शुक्ला भाद्रपदे मासि दूर्वासंज्ञा तथाष्टमी। सिंहार्क एव कर्तव्या न कन्यार्के कदाचन॥" | 227–230 | H |
| jyeṣṭhā-gaurī / nīla-jyeṣṭhā | NEW `jyESThA-gaurI-vratam` (+`nIla-jyESThA-yOgaH`) | 06/08 (+jyeṣṭhā; +ravivāra) | "भाद्रशुक्लाष्टमी ज्येष्ठानक्षत्रेण समन्विता। महती कीर्तिता तस्यां ज्येष्ठां देवीं प्रपूजयेत्। उपहारैर्बहुविधैरलक्ष्मीविनिवृत्तये॥"; "तत्राष्टम्यां यदा भानोर्वारो ज्येष्ठर्क्षमेव च। नीलज्येष्ठेति सा प्रोक्ता दुर्लभा बहुकालिका॥"; "ज्येष्ठायै ते नमस्तुभ्यं श्रेष्ठायै ते नमो नमः। शर्वाय ते नमस्तुभ्यं शाङ्कर्यै ते नमो नमः॥" | 230–231 | M/H (C3) |
| mahālakṣmī-vrata | FIX (start 06/08, end 06/23) + ADD | 06/08 → 06/23 candrodaya | "धियोऽर्चनं भाद्रपदे सिताष्टमीं प्रारभ्य कन्यामगते च सूर्ये। समापयेत्तत्र तिथौ च यावत्सूर्यस्तु पूर्वार्धगतो युवत्याः॥"; "त्रिदिने चावमे चैव अष्टमी नोपवासयेत्। पुत्रघ्नी नवमी विद्धा स्वघ्नी हस्तार्धगे रवौ॥" | 231–239 | H (doṣas) |
| `nandA~navamI` | ADD-SH (none now) | 06/09 | "मासि भाद्रपदे या स्यान्नवमी बहुलेतरा। सा तु नन्दा महापुण्या कीर्तिता पापनाशिनी। तस्यां यः पूजयेद्दुर्गां विधिवत्कुरुनन्दन। सोऽश्वमेधफलं विन्द्याद्विष्णुलोकं च गच्छति॥" | 239 | S |
| `dazAvatAra-vratam` | ADD-SH | 06/10 | "मत्स्यं कूर्मं वराहं च नारसिंहं त्रिविक्रमम्। रामं रामं च कृष्णं च बौद्धं चैव सकल्किनम्। गतोऽस्मि शरणं देवं हरिं नारायणं प्रभुम्…" | 239–240 | S |
| `kaTadAnOtsavaH` | ADD-SH (none now) | 06/11 | "प्राप्ते भाद्रपदे मासि एकादश्यां सितेऽहनि। कटदाने भवेद्विष्णोर्महापातकनाशनम्॥"; "देवदेव जगन्नाथ योगिगम्य निरञ्जन। कटदानं करिष्येऽद्य प्राप्ते भाद्रपदे शुभे॥" | 240 | S |
| śravaṇa-dvādaśī (+budha) | ADD-SH to `zravaNa-mahAdvAdazI`; NEW `budha-zravaNa-dvAdazI` | 06/12 ∧ śravaṇa (∧ budha) | "श्रीराम श्रवणोपेता द्वादशी महती तु या…प्राप्नोत्ययत्नाद्धर्मज्ञ द्वादशद्वादशीफलम्॥"; "बुधश्रवणसंयुक्ता सैव चेद्द्वादशी भवेत्। अतीव महती तस्यां कृतं सर्वमिहाक्षयम्…" | 240–249 | M |
| `vAmana~jayantI` | ADD-SH | 06/12 madhyāhna pūrva | "श्रोणायां श्रवणद्वादश्यां मुहूर्तेऽभिजिति प्रभुः…विजया नाम सा प्रोक्ता यस्यां जन्म विदुर्हरेः॥"; arghya "वामनाय नमस्तुभ्यं क्रान्तं त्रिभुवनं यतः। गृहाणार्घ्यं मया दत्तं वामनाय नमो नमः॥" | 249–250 | S |
| 8 mahādvādaśīs | ADD-SH (vyaJjulI, gOvinda have none) | – | "उन्मीलिनी वञ्जुली च त्रिस्पृशा पक्षवर्धिनी। जया च विजया चैव जयन्ती पापनाशिनी…"; va~njulī niyama "द्वादश्यां तु निराहारः पारणं वा परेऽहनि। धर्मार्थकाममोक्षार्थं करिष्ये वञ्जुलीव्रतम्॥" | 250–254 | LOW |
| `zakradhvajotthApanam` | ADD-SH | 06/12 (+uttarāṣāḍhā, kanyā-ravi) | "द्वादश्यां च सिते पक्षे मासि भाद्रपदे तथा। शक्रमुत्थापयेद्राजा विश्वनक्षत्रसंयुजि…" | 254 | M |
| `payOvrata-ArambhaH` | ADD-SH | 06/12 night | dugdha-vrata saṅkalpa; forbidden milks (Śaṅkha) | 254 | S |
| ananta-vrata | FIX/ADD (`ananta-caturdazI`, `ananta-padmanAbha-vratam` both no shlokas) | 06/14 udaya+3 muhūrta; pūrṇimā-yoga | "उदये त्रिमुहूर्तापि ग्राह्याऽनन्तव्रते तिथिः"; "भाद्रपदस्यान्ते चतुर्दश्यां द्विजोत्तम। पौर्णमास्याः समायोगे व्रतं चानन्तकं चरेत्॥"; "आगच्छानन्त देवेश तेजोराशे जगत्पते…"; "अनन्तानन्त देवेश अनन्तगुणसागर। अनन्तानन्तरूपोऽसि गृहाणार्घ्यं नमोऽस्तु ते॥" | 254–286 | S |
| prauṣṭhapadī nāndīmukha-śrāddha | NEW-CODE (C9) | 06/15 if kanyā-saṅkrānti falls in bhādra | "नान्दीमुखानां प्रत्यब्दं कन्याराशिगते रवौ। पौर्णमास्यां तु कर्तव्यं वराहवचनं यथा॥"; "पौर्णमासीषु सर्वासु निषिद्धं पिण्डपातनम्। वर्जयित्वा प्रौष्ठपदीं यथा दर्शस्तथैव सा॥" | 270 | H |
| mahālaya family | ADD-SH to `mahAlaya-pakSa*` + NEW alternates | 06/16–30 | "आश्वयुक्कृष्णपक्षे तु श्राद्धं कार्यं दिने दिने। त्रिभागहीनं पक्षं वा त्रिभागं त्वर्धमेव वा॥"; "कन्यागते सवितरि यान्यहानि तु षोडश। क्रतुभिस्तानि तुल्यानि देवो नारायणोऽब्रवीत्॥"; "मध्ये वा यदि वाप्यन्ते यत्र कन्यां व्रजेद्रविः। स पक्षः सकलः श्रेष्ठः श्राद्धषोडशकं प्रति॥"; gauṇa: "यावच्च कन्यातुलयोः क्रमादास्ते दिवाकरः। तावच्छ्राद्धस्य कालः स्याच्छून्यं प्रेतपुरं तदा॥"; "हंसे वर्षासु कन्यास्थे शाकेनापि गृहे वसन्। पञ्चम्योरन्तरे दद्यादुभयोरपि पक्षयोः॥"; last resort: "येयं दीपान्विता राजन्ख्याता पञ्चदशी भुवि। तस्यां दद्यान्न चेद्दत्तं पितॄणां वै महालये॥" | 271–274 | M |
| mahālaya alt. starts & end-bounds | NEW (5 start points; gauṇa-end at vṛścika-saṅkrānti; āśvina ś5; dīpāvalī amā) | – | as above | 271–272 | M |
| `yati-mahAlayam` | ADD-SH (none now) | 06/27 | "यतीनां च वनस्थानां वैष्णवानां विशेषतः। द्वादश्यां विहितं श्राद्धं कृष्णपक्षे विधीयते॥" | 273 | S |
| `zastrahatacaturdazI` | ADD-SH | 06/29 aparāhṇa | "समत्वमागतस्यापि पितुः शस्त्रहतस्य वै। एकोद्दिष्टं तु कर्तव्यं चतुर्दश्यां महालये॥"; "प्रायोऽनशनशस्त्राग्निविषोद्बन्धनिनां तथा। चतुर्दश्यां तु कर्तव्यम्…" | 274, 279–280 | S |
| `mahAbharaNI` | verify shloka | bhādra kṛṣṇa bharaṇī | "भरणी प्रेतपक्षे तु महती परिकीर्तिता। अस्यां श्राद्धं कृतं येन स गयाश्राद्धकृद्भवेत्॥" | 274 | – |
| `madhyASTamI` (= mādhyāvarṣa) | ADD-SH (none now) | 06/23 aparāhṇa (7-8-9 like aṣṭakā) | Āśv. "एतेन माध्यावर्षं प्रोष्ठपद्या अपरपक्षे"; kātīya "प्रथमाष्टकापक्षाष्टम्याम्" | 274 | S |
| `avidhavA-navamI` | ADD-SH | 06/24 aparāhṇa | "सर्वासामेव मातॄणां श्राद्धं कन्यागते रवौ। नवम्यां हि प्रदातव्यं प्राप्तब्रह्मवराय ते॥"; "भर्तुरग्रे मृता नारी सहदाहेन वा मृता। तस्याः स्थाने नियुञ्जीत विप्रैः सह सुवासिनीम्॥" | 275–276 | S |
| maghā-trayodaśī / gajacchāyā | NEW `maghA-trayOdazI-zrAddham` (06/28 ∧ maghā); verify `gajacchAyA-yOgaH` def (sun in hasta) | – | "प्रोष्ठपद्यामतीतायां मघायुक्तां त्रयोदशीम्। प्राप्य श्राद्धं तु कर्तव्यं मधुना पायसेन वा…"; "हंसे हंसस्थिते या तु मघायुक्ता त्रयोदशी। तिथिर्वैवस्वती नाम सा छाया कुञ्जरस्य तु॥"; amā variant "हंसे हंसस्थिते या तु अमावास्या करान्विता। सा ज्ञेया कुञ्जरच्छाया…" | 276–280 | M/H |
| `dauhitra-pratipat` | FIX (aparāhṇa) + ADD | 07/01 | "जातमात्रोऽपि दौहित्रो विद्यमानेऽपि मातुले। कुर्यान्मातामहश्राद्धं प्रतिपद्याश्विने सिते॥" | 280–281 | S |
| `kapila-SaSThI` | FIX (C2) + ADD | 06/21 ∧ bhauma ∧ vyatīpāta ∧ rohiṇī (∧ sun in hasta) | "प्रौष्ठपदासिते पक्षे षष्ठी भौमेन संयुता। व्यतीपातेन रोहिण्या सा षष्ठी कपिला स्मृता॥"; "अस्मिन्योगे समस्ते स्यान्नाडिकापि यदा तिथिः। यदि हस्ते सहस्रांशुस्तदा कार्यं व्रतं बुधैः॥"; dāna "नमस्ते कपिले देवि सर्वपापप्रणाशिनि। संसारार्णवमग्नं मां गोमातस्त्रातुमर्हसि॥" | 281–287 | M/H |

### 5.7 Āśvina (आश्विनकृत्यम्, pp.287–358)

| Item | Status | Timing | Key shloka(s) | p. | Cx |
|---|---|---|---|---|---|
| `Azvina-mAsa-ArambhaH` | ADD-SH | month | Yama "घृतमाश्वयुजे मासि नित्यं दद्याद्द्विजातये। प्रीणयित्वाश्विनौ देवौ रूपभागभिजायते॥"; Vāmana "तिलांस्तुरङ्गं वृषभं दधि ताम्रं वशादिकम्। प्रीत्यर्थं पद्मनाभस्य देयमाश्वयुजे नरैः॥" | 287 | S |
| `zarannavarAtra-ArambhaH` | ADD-SH (none now) + document timing dispute | 07/01; SK: **pradoṣa-vyāpinī**, amā-viddhā acceptable; Gauḍa: udaya-gāminī | Rudrayāmala "आश्विने मासि संप्राप्ते शुक्लपक्षे विधेस्तिथिम्। प्रारभ्य नवरात्रं स्याद्दुर्गा पूज्या तु तत्र वै॥"; Dhaumya "आश्विने शुक्लपक्षे तु कर्तव्यं नवरात्रकम्। प्रतिपदादिक्रमेणैव यावद्धि नवमी भवेत्॥"; Devī-P "मासि चाश्वयुजे शुक्ले नवरात्रं विशेषतः। संपूज्य नवदुर्गां च नक्तं कुर्यात्समाहितः॥"; kalaśa: "आद्याः षोडश नाडीस्तु लब्ध्वा यः कुरुते नरः। कलशस्थापनं तत्र अरिष्टं जायते ध्रुवम्॥"; Gauḍa "शरत्काले महापूजा क्रियते या च वार्षिकी। सा कार्योदयगामिन्यां न तत्र तिथियुग्भवेत्॥" | 287–297 | M (keep kaala as-is; add a `description` para on both views; optional variant id for the SK/pradoṣa view) |
| navarātra anukalpas | NEW (LOW) `saptarAtra-…` 07/03, `paJcarAtra-…` 07/05, `trirAtra-…` 07/07, `ekarAtra` 07/08 | – | "एकभक्तस्तु पञ्चम्यां षष्ठ्यां नक्तं प्रवर्तयेत्। अयाचितस्तु सप्तम्यामष्टम्यां समुपोषितः। नवम्यां पारणं कुर्यात्पञ्चरात्रमितीरितम्॥" | 290–292 | S |
| aśva-pūjā / vājinīrājana | NEW (LOW, royal) `azva-pUjA` | 07/01–09, prefer svātī | "आश्वयुक्शुक्लपक्षे तु स्वातीयोगे शुभे दिने। पूर्वमुच्चैःश्रवा नाम प्रथमं सूर्यवाहनम्…पूजनीयाश्च तुरगा नवमी यावदेव हि॥"; "ततो नीराजनं कर्म प्रतिपद्याश्विने सिते। प्रारभ्य नवरात्रं स्याद्धित्वा चित्रां च वैधृतिम्॥" | 296, 335–343 | M |
| kumārī-pūjā | description on navarātra entries | – | "पितरो वसवो रुद्रा आदित्या गणलोकपाः। सर्वे ते पूजितास्तेन कुमार्यो येन पूजिताः॥" (+ age-names kumārī/trimūrti/kalyāṇī…) | 303–306 | – |
| bilva-bodhana | NEW `bilva-bOdhanam` (2 variants) | (a) 06/24 ∧ ārdrā, pūrvāhṇa; (b) 07/06 sāyāhna ∧ jyeṣṭhā | Liṅga "कन्यायां कृष्णपक्षे तु पूजयित्वार्द्रभे दिवा। नवम्यां बोधयेद्देवीं महाविभवविस्तरैः॥"; Devī-P "ज्येष्ठानक्षत्रयुक्तायां कुर्याद्बिल्वाभिमन्त्रणम्"; Brahmāṇḍa "पत्रीप्रवेशात्पूर्वेद्युः सायाह्ने बिल्ववासिनीम्। चण्डीमामन्त्रयेद्विद्वान्नात्र षष्ठीपुरस्क्रिया॥"; "अमृतोद्भवः श्रीवृक्षः शंकरस्य सदा प्रियः। बिल्वपत्रं प्रयच्छामि पवित्रं ते सुरेश्वरि॥" | 307–310 | M |
| `patrikA-pravEza-pUjA` | ADD-SH (none now); udaya-gāminī, mūla preferred but never at night | 07/07 | Nandi-P "भगवत्याः प्रवेशादि विसर्गान्ताश्च याः क्रियाः। तिथावुदयगामिन्यां सर्वास्ताः कारयेद्बुधः॥"; "ऋक्षयोगानुरोधेन रात्रौ पत्रीप्रवेशनम्। विसर्गं वाचरेद्यस्तु सराष्ट्रः स विनश्यति॥" | 307–310 | S |
| `durgASTamI` | FIX (udaya; reject saptamī-vedha) + ADD | 07/08 | "नवमीसंयुता कार्या सदा दुर्गाष्टमी बुधैः। सप्तमीसंयुता हन्ति पूर्वपुण्यकृतं फलम्॥"; "सप्तमीस्वल्पसंबन्धा वर्जनीया सदाष्टमी। स्तोकापि सा तिथिः पुण्या यस्यां सूर्योदयो भवेत्॥" | 311–312 | S |
| `mahAnavamI_or_sarasvatI-pUjA` | FIX (pūrvaviddhā) + ADD | 07/09 | "आश्वयुक्शुक्लपक्षे तु नवमी पूर्वसंयुता। सा महानवमी प्रोक्ता…" | 311–312 | S |
| navamī-bali | NEW (LOW) `navamI-baliH` (daśamī-viddhā) | 07/09 | "सूर्योदये परं रिक्ता पूर्णा स्यादपरा यदि। बलिदानं प्रकर्तव्यं…" | 312 | M |
| durgā-visarjana | NEW `durgA-visarjanam` + ADD-SH to `durgA-pUjA` 07/10 | 07/10 day; prefer day with last pāda of śravaṇa | Dhavala-nibandha "अन्त्यपादो दिवा भागे श्रवणस्य यदा भवेत्। संप्रेषणं तदा देव्या दशम्यां तु पुनर्दिवा॥"; "उत्तिष्ठ देवि चण्डेशि शुभां पूजां प्रगृह्य च…"; "दुर्गे देवि जगन्मातः स्वस्थानं गच्छ पूजिते। संवत्सरे व्यतीते तु पुनरागमनाय वै॥" | 324 | M (nakshatra_pada) |
| `zarannavarAtra-samApanam` / pāraṇa | ADD-SH; note navamī (dākṣiṇātya) vs daśamī (prācya) | 07/09|07/10 | Brahmāṇḍa "आश्विने शुक्लपक्षे तु नवरात्रमुपोषितः। नवम्यां पारणं कुर्याद्दशमीसहिता न चेत्॥"; Rudrayāmala "नवम्यां पारिता देवी कुलवृद्धिं प्रयच्छति। दशम्यां पारिता देवी कुलनाशं करोति हि॥" | 325–327 | S |
| lohābhisārika | NEW (LOW, royal) | 07/01–08 | Bhaviṣyottara chatra/cāmara/aśva mantras | 331–335 | S |
| `upAGga-lalitA-vratam` | FIX (pūrvaviddhā, aparāhṇa) + ADD | 07/05 | "गर्जितं संध्ययोस्त्याज्यं दिनवृद्धिक्षयौ तथा" (+ apāmārga mantras) | 343–352 | S |
| sarasvatī āvāhana → visarjana | FIX (`sarasvatI-visarjanam` nakṣatra 21→22) + NEW `sarasvatI-baliH` (21) + ADD-SH to all 4 | mūla → pū.āṣāḍhā → u.āṣāḍhā → śravaṇa, pūrvaviddha | Saṅgraha "आश्विनस्य सिते पक्षे मेधाकामः सरस्वतीम्। मूलेनावाहयेद्देवीं पूर्वाषाढासु पूजयेत्। उत्तरासु बलिं दद्याच्छ्रवणेन विसर्जयेत्॥"; anadhyāya "नाध्यापयेन्न च लिखेन्नाधीयीत कदाचन। पुस्तके स्थापिते दैवे…" | 352 | S |
| aparājitā-pūjā / sīmollaṅghana | NEW `aparAjitA-pUjA`, `sImOllaGghanam` (C3) | 07/10 aparāhṇa; śravaṇa-override; else navamī-viddhā; never on ekādaśī | Skanda "दशम्यां तु जनैः सम्यक्पूजनीयाऽपराजिता। ऐशानीं दिशमाश्रित्य अपराह्णे प्रयत्नतः॥"; Kaśyapa "उदये दशमी किंचित्संपूर्णैकादशी यदि। श्रवणर्क्षं यदा काले सा तिथिर्विजयाभिधा। श्रवणर्क्षे तु पूर्णायां काकुत्स्थो निर्गतो यतः। उल्लङ्घयेयुः सीमानं तद्दिनर्क्षे ततो नराः॥"; "नवमीशेषयुक्तायां दशम्यामपराजिता। ददाति विजयं देवी…"; "एकादश्यां न कुर्वीत पूजनं चापराजितम्" | 352–354 | M/H |
| `vijayadazamI_yAtrA` | ADD-SH (vijaya-muhūrta) | 07/10 sāyam | Bhṛgu "आश्विनस्य सिते पक्षे दशम्यां सर्वरात्रिषु। सायंकाले शुभा यात्रा दिवा वा विजयक्षणे॥"; "ईषत्संध्यामतिक्रान्तः किंचिदुद्भिन्नतारकः। विजयो नाम कालोऽयं सर्वकार्यार्थसाधकः॥"; "एकादशो मुहूर्तोऽपि विजयः परिकीर्तितः" | 353 | S |
| `zamI-pUjA` | REVIEW kaala (SK: aparāhṇa with aparājitā) + ADD | 07/10 | "अमङ्गलानां शमनीं शमनीं दुष्कृतस्य च। दुःस्वप्ननाशिनीं धन्यां प्रपद्येऽहं शमीं शुभाम्॥"; "शमी शमयते पापं शमी लोहितकण्टका। धारिण्यर्जुनबाणानां रामस्य प्रियवादिनी॥" | 353–354 | S |
| Āśvina ś11–15 vaiṣṇava pañcaka | description / ADD to `zakradhvajapAtaH`-area entries | 07/11–15 | "सोपवासश्च कर्तव्य एकादश्यां प्रजागरः। द्वादश्यां वासुदेवस्य पूजनीयश्च सर्वदा। यात्रोत्सवश्च कर्तव्यस्त्रयोदश्यां तु वैष्णवैः। उपवासश्चतुर्दश्यां पौर्णमास्यां हरिं यजेत्॥" | 355 | LOW |
| `kO-jAgarti-vratam` (+`lakSmI-indra-kubEra-pUjA`, `kaumudI-utsavaH`) | ADD-SH (exists, niśītha para — OK) | 07/15 | Bharata "पूर्णिमा चाश्विने मासि कौमुदी परिकीर्तिता। कौमुद्यां पूजयेल्लक्ष्मीमिन्द्रमैरावतस्थितम्। निशि जागरणं कृत्वा परेद्युरुत्सवमाचरेत्॥" | 355 | S |
| āśvayujī + aśvinī ghṛta-pātra dāna | NEW (family §6.4) | 07/15 ∧ aśvinī | "आश्वयुज्यामश्विनीगतेन चन्द्रमसा घृतपूर्णपात्रं सुवर्णयुक्तं विप्राय दत्त्वा दीप्ताग्निर्भवति" | 355 | M |
| āśvayujī-karma (Āśvalāyana) | NEW `AzvayujI-karma` (gRhya) | 07/15, pūrṇimā-parva rules | Āśv. gṛhya 2.2 (pṛṣātaka) | 355–357 | M |
| `apatya-nIrAjanam` | verify priority (SK: paraviddhā) + ADD ref | 07/15 | ācāra | 357 | S |

### 5.8 Kārtika (कार्तिककृत्यम्, pp.358–426)

| Item | Status | Timing | Key shloka(s) | p. | Cx |
|---|---|---|---|---|---|
| `kArttika-mAsa-ArambhaH` | ADD-SH | month | Viṣṇu "कार्तिकं सकलं मासं नित्यस्नायी जितेन्द्रियः। जपन्हविष्यभुग्दान्तः सर्वपापैः प्रमुच्यते॥"; Vāmana "राजतं काञ्चनं दीपान्मणिमुक्ताफलादिकम्। दामोदरस्य प्रीत्यर्थं प्रदद्यात्कार्तिके नरः॥"; hari-jāgara "जागरं कार्तिके मासि यः कुर्यादरुणोदये…" | 358, 361 | S |
| ākāśa-dīpa start | NEW `AkAzadIpa-ArambhaH` + ADD-SH to `AkAzadIpa-samApanam` | 07/15 pradoṣa → 08/15 | "पूर्ण आश्वयुजे मासि पौर्णमास्यां समाहितः। प्रथमे च निशारम्भे मनोवाक्कायसंयतः। नमः पितृभ्यः प्रेतेभ्यो नमो धर्माय विष्णवे। नमो यमाय रुद्राय कान्तारपतये नमः॥"; "दामोदराय नभसि तुलायां दोलया सह। प्रदीपं ते प्रयच्छामि नमोऽनन्ताय वेधसे॥" | 358–359 | S |
| kārtika-snāna | NEW `kArttika-snAna-ArambhaH` (07/10 | 07/11 | 07/15) + FIX `kArttika-snAnapUrtiH` 08/30→08/15 | aruṇodaya | arghya "नमः कमलनाभाय नमस्ते जलशायिने। नमस्तेऽस्तु हृषीकेश गृहाणार्घ्यं नमोऽस्तु ते॥"; saṅkalpa "कार्तिकेऽहं करिष्यामि प्रातःस्नानं जनार्दन। प्रीत्यर्थं तव देवेश दामोदर मया सह॥" | 360, 389 | S |
| dhātrī-pūjā / vana-bhojana | ADD-SH to `akSayA~navamI` (+ optional NEW `dhAtrI-bhOjanam`) | 08/09 (any kārtika day) | Skanda "कार्तिके मासि विप्रेन्द्र धात्रीवृक्षोपशोभिते…"; Padma "अनेन विधिना यस्तु कार्तिक्यां पूजयेद्धरिम्…" | 360–366 | S |
| `tulasI-vivAhOtsava-*` | ADD SK alternates (uttarāyaṇa w/ guru-śukra udaya; bhīṣma-pañcaka days; pūrṇimā; lagna after sunset) + 24-nāma homa | 08/09–08/12 (+08/15) | Viṣṇuyāmala (p.366) | 366 | S |
| `karaka-caturthI` | ADD rule + shloka; kaala → candrodaya | 07/19 | "कार्तिके कृष्णपक्षे तु…चन्द्रोदयव्यापिनी…" | 367 | S |
| rādhā-kuṇḍa-snāna | NEW `rAdhAkuNDa-snAnam` | 07/23 aruṇodaya | (Mathurā-māhātmya) | 367 | S |
| `gOvatsa-dvAdazI` | ADD-SH (exists, pradoṣa OK) | 07/27 | "संप्राप्ते कार्तिके मासि कृष्णपक्षे कुरूत्तम। द्वादश्यां कृतसंकल्पः स्नात्वा पुण्यजलाशये…"; "क्षीरोदार्णवसंभूते सुरासुरनमस्कृते। सर्वदेवमये मातर्गृहाणार्घ्यं नमो नमः॥"; "सुरभि त्वं जगन्मातर्देवि विष्णुपदे स्थिता। सर्वदेवमये ग्रासं मया दत्तमिमं ग्रस॥" | 367–368 | S |
| nṛpa-nīrājana 5 days | NEW (LOW) | 07/27–08/01 pūrvarātra | Nāradīya "आश्विने कृष्णपक्षे च द्वादश्यादिषु पञ्चसु। तिथिषूक्तः पूर्वरात्रे नृपनीराजनाविधिः…" | 368 | S |
| `(yama)-dIpa-trayOdazI` | ADD-SH | 07/28 pradoṣa | Skanda "कार्तिकस्यासिते पक्षे त्रयोदश्यां निशामुखे। यमदीपं बहिर्दद्यादपमृत्युर्विनश्यति॥"; "मृत्युना पाशदण्डाभ्यां कालेन श्यामया सह। त्रयोदश्यां दीपदानात्सूर्यजः प्रीयतां मम॥" | 368 | S |
| `gO-trirAtra-vratam~2` | ADD-SH (none now); verify `~1` (06/13) source | 07/28–30 | "गोविन्द जगतां नाथ गोवर्धनधरानघ। गोत्रिरात्रं करिष्यामि शरणं मे भवाच्युत॥" | 368–370 | S |
| `naraka-caturdazI-snAnam` | ADD-SH + note rules (candrodaya mukhya; uṣaḥkāla partial OK; amā-fallback with svātī) | 07/29 | "कार्तिके कृष्णपक्षे तु चतुर्दश्यां विधूदये। तिलतैलेन कर्तव्यं स्नानं नरकभीरुभिः॥"; "तैले लक्ष्मीर्जले गङ्गा दीपावल्यां चतुर्दशी…"; apāmārga "सीतालोष्ठसमायुक्त सकण्टकदलान्वित। हर पापमपामार्ग भ्राम्यमाणः पुनः पुनः॥"; "इषासिते चतुर्दश्यामिन्दुक्षयतिथावपि। ऊर्जादौ स्वातिसंयुक्ते तदा दीपावलिर्भवेत्॥" | 370–373 | S |
| `dIpOtsava-caturdazI_or_yama-tarpaNam` | ADD-SH (yama-tarpaṇa incl. jīvat-pitṛka; pradoṣa dīpa) | 07/29 | "अग्निर्ज्योती रविर्ज्योतिश्चन्द्रो ज्योतिस्तथैव च। उत्तमः सर्वज्योतीनां दीपोऽयं प्रतिगृह्यताम्॥" | 371 | S |
| ulkā-dāna | NEW `ulkA-dAnam` (C9: sun in tulā) | 07/29 & 07/30 pradoṣa | Jyotirnibandha "तुलासंस्थे सहस्रांशौ प्रदोषे भूतदर्शयोः। उल्काहस्ता नराः कुर्युः पितॄणां मार्गदर्शनम्॥" | 372 | S/M |
| `dIpAvalI_or_lakSmI-kubEra-pUjA` | ADD-SH (none now); rule: pradoṣa-vyāpinī amā | 07/30 | Āditya-P "प्रदोषसमये लक्ष्मीं पूजयित्वा यथाक्रमम्। दीपवृक्षास्तथा कार्याः…"; "नमस्ते सर्वदेवानां वरदासि हरिप्रिये। या गतिस्त्वत्प्रपन्नानां सा मे भूयात्त्वदर्चनात्॥"; kubera "धनदाय नमस्तुभ्यं निधिपद्माधिपाय च। भवन्तु त्वत्प्रसादान्मे धनधान्यादिसंपदः॥"; Padma "गृहस्थेन प्रकर्तव्यं रात्रौ भोजनमङ्गलम्। दिवा श्राद्धं प्रकर्तव्यं…" | 373 | S |
| alakṣmī-niṣkāsana | NEW `alakSmI-niSkAsanam` | 07/30 niśītha | "एवं गते निशीथे च जने निद्रार्तलोचने। तावन्नगरनारीभिस्तूर्यडिण्डिमनिस्वनैः। निष्काश्यते प्रहृष्टाभिरलक्ष्मीः स्वगृहाङ्गणात्॥" | 373 | S |
| `gOvardhana-pUjA` | FIX (prātaḥ; moon-seen rule C6) + ADD | 08/01 | Skanda "प्रातर्गोवर्धनः पूज्यो द्यूतं चापि समाचरेत्। भूषणीयास्तथा गावः पूज्या वाहदोहनाः॥"; "गोवर्धन धराधार गोकुलत्राणकारक। विष्णुबाहुकृतच्छाय गवां कोटिप्रदो भव॥"; "लक्ष्मीर्या लोकपालानां धेनुरूपेण संस्थिता। घृतं वहति यज्ञार्थे मम पापं व्यपोहतु॥"; "गवां क्रीडादिने यत्र रात्रौ दृश्येत चन्द्रमाः। सोमो राजा पशून्हन्ति सुरभीपूजकांस्तथा॥"; "त्रियामिका दर्शतिथिर्भवेच्चेत्सार्धत्रियामा प्रतिपद्विवृद्धौ। दीपोत्सवे ते मुनिभिः प्रदिष्टे अतोऽन्यथा पूर्वयुते विधेये॥" | 374–375 | M (C6) |
| mārgapālī | NEW `mArgapAlI-bandhanam` | 08/01 aparāhṇa, pūrvaviddhā | "मार्गपालीं प्रबध्नीयात्तुङ्गे स्तम्भेऽथ पादपे…"; "मार्गपालि नमस्तेऽस्तु सर्वलोकसुखप्रदे। विधेयैः पुत्रदाराद्यैः पुनरेहि व्रतस्य मे॥" | 375–376 | S |
| dyūta / vartikā-karṣaṇa | NEW (LOW) | 08/01 prātaḥ | – | 375–376 | S |
| `bali_pratipat` | FIX (split: night bali-pūjā pūrvaviddhā vs sunrise abhyaṅga) + ADD | 08/01 | "बलिराज नमस्तुभ्यं विरोचनसुत प्रभो। भविष्येन्द्र सुराराते पूजेयं प्रतिगृह्यताम्॥"; "बलिमुद्दिश्य दीयन्ते दानानि कुरुनन्दन। यानि तान्यक्षयाण्याहुः…"; "श्रावणी दुर्गनवमी दूर्वा चैव हुताशनी। पूर्वविद्धा प्रकर्तव्या शिवरात्रिर्बलेर्दिनम्॥" | 376 | M |
| nārī-nīrājana / maṅgala-mālikā | NEW `nArI-nIrAjanam` | 08/01 prātaḥ (pratipat ≥2 ghaṭī, else dvitīyā) | "नारीनीराजनं प्रातः सायं मङ्गलमालिका…" | 377 | M |
| `yama_or_bhrAtR-dvitIyA` | ADD-SH (aparāhṇa para OK) | 08/02 | Skanda "ऊर्जशुक्लद्वितीयायामपराह्णेऽर्चयेद्यमम्। स्नानं कृत्वा भानुजायां यमलोकं न पश्यति॥"; "एह्येहि मार्तण्डज पाशहस्त यमान्तकालोकधरामरेश। भ्रातृद्वितीयाकृतदेवपूजां गृहाण चार्घ्यं भगवन्नमस्ते॥"; Liṅga "कार्तिके तु द्वितीयायां शुक्लायां भ्रातृपूजनम्। या न कुर्याद्विनश्यन्ति भ्रातरः सप्तजन्मसु॥" | 377–378 | S |
| mahā-ṣaṣṭhī | NEW `mahA-SaSThI~kArttika` (C9) | 08/06 ∧ bhauma ∧ sun in vṛścika | Matsya "वृश्चिके शुक्लषष्ठ्यां तु भौमवारे ह्युपस्थिते। महाषष्ठीति सा प्रोक्ता सर्वपापहरा तिथिः। तस्यां स्वपिति वै वह्निः…" | 378 | M |
| `gOpASTamI` | verify shloka | 08/08 | "कार्तिके याष्टमी शुक्ला ज्ञेया गोपाष्टमी बुधैः। तत्र कुर्याद्गवां पूजां गोग्रासं गोप्रदक्षिणम्। गवानुगमनं कार्यं सर्वान्कामानभीप्सता॥" | 378 | – |
| mathurā-pradakṣiṇā | NEW (regional) | 08/09 | Varāha | 378 | S |
| `prabOdhOtsavaH` | ADD (abhiṣeka on ś12 aruṇodaya) | 08/12 | Brahma (p.379) | 379 | S |
| `bhISma-paJcaka-vrata-*` | ADD-SH; pañcagavya per day (gomaya 11, gomūtra 12, kṣīra 13, dadhi 14) | 08/11–15 | Devī-P "एकादश्यां तु गृह्णीयाद्व्रतं पञ्चदिनात्मकम्…" | 385–388 | S |
| vṛṣotsarga | NEW `vRSOtsargaH` (+07/15 ∧ revatī, 01/15, 02/15 ∧ revatī alternates) | 08/15 | "कार्तिक्यां तु वृषोत्सर्गो विवाहः शुभलक्षणः। कार्यः कुरुकुलश्रेष्ठ हरेर्नीराजनं तथा॥"; Matsya "कार्तिक्यां यो वृषोत्सर्गं कृत्वा नक्तं समाचरेत्। शैवं पदमवाप्नोति…"; "एष्टव्या बहवः पुत्रा यद्येकोऽपि गयां व्रजेत्। यजेत वाश्वमेधेन नीलं वा वृषमुत्सृजेत्॥" | 390–406 | M |
| kṛttikā-pūjā / kṣīrasāgara-dāna | NEW `kRttikA-pUjA`, `kSIrasAgara-dAnam` | 08/15 niśāgama | "तप्तहेममयो मत्स्यो मुक्तानेत्रो मनोहरः… नमोऽस्तु हरये…" | 406 | S |
| `mahA~kArttikI` | FIX (tie to pūrṇimā; rohiṇī = mahā-kārtikī; kṛttikā = mahā-puṇyā; guru+candra in kṛttikā C2) + ADD | 08/15 ∧ nakṣatra | "आग्नेयं तु यदा ऋक्षं कार्तिक्यां भवति क्वचित्। तिथिः सापि महापुण्या मुनिभिः परिकीर्तिता। प्राजापत्यं यदा ऋक्षं तिथौ तस्यां नराधिप। सा महाकार्तिकी प्रोक्ता देवानामपि दुर्लभा॥"; "पुण्या महाकार्तिकी स्याज्जीवेन्द्वोः कृत्तिकास्थयोः" | 406 | M (C2 for guru) |
| `padmaka-yOga*` | ADD SK ref/shloka; verify definition | – | "विशाखासु यदा भानुः कृत्तिकासु च चन्द्रमाः। स योगः पद्मको नाम पुष्करेष्वपि दुर्लभः॥" | 406 | S |
| `tripurOtsavaH` | ADD-SH (none now) | 08/15 sandhyā | Bhaviṣya "पौर्णमास्यां तु संध्यायां कर्तव्यस्त्रिपुरोत्सवः। दद्यादनेन मन्त्रेण सुदीपांश्च सुरालये॥ कीटाः पतङ्गा मशकाश्च वृक्षा जले स्थले ये विचरन्ति जीवाः। दृष्ट्वा प्रदीपं नहि जन्मभागिनो भवन्ति नित्यं श्वपचा हि विप्राः॥" | 426 | S |
| kārtika udyāpanas (lakṣa-pradakṣiṇā, varti, dhāraṇa-pāraṇa…), gopadma, śayyā-dāna | SKIP (description only at most) | – | – | 406–424 | – |

### 5.9 Mārgaśīrṣa (मार्गशीर्षकृत्यम्, pp.427–432)

| Item | Status | Timing | Key shloka(s) | p. | Cx |
|---|---|---|---|---|---|
| `mArgazIrSa-mAsa-ArambhaH` | ADD-SH | month | MBh "मार्गशीर्षं तु यो मासमेकभक्तेन संक्षिपेत्। भोजयेच्च द्विजान्भक्त्या स मुच्येद्व्याधिकिल्बिषैः॥" | 427 | S |
| `kAlabhairavASTamI` (+ `kAlASTamI`) | FIX (pūrvaviddhā) + ADD-SH | 08/23 pradoṣa | Śivarahasya "कालाष्टमीति विज्ञेया कार्तिकस्यासिताष्टमी। तस्यामुपोषणं कार्यं तथा जागरणं निशि॥ भैरवस्य तु कर्तव्या पूजा यामचतुष्टये…"; Kāśīkhaṇḍa "मार्गशीर्षासिताष्टम्यां कालभैरवसंनिधौ। उपोष्य जागरं कुर्यान्महापापैः प्रमुच्यते॥"; "यो देवि भैरवाष्टम्यामुपवासं प्रयत्नतः। न करिष्यति मोहेन यास्यत्येवेह यातनाम्॥"; arghya "भैरवार्घ्यं गृहाणेश भीमरूपाव्ययानघ। अनेनार्घ्यप्रदानेन तुष्टो भव शिवप्रिय॥" | 427–429 | S |
| mārgaśīrṣa nāga-pūjā | NEW `mArgazIrSa-nAga-paJcamI` (paraviddha) + verify `sarpa-pUjA~2` (08/05) source | 09/05 | Skanda "शुक्ला मार्गशिरे पुण्या श्रावणे या च पञ्चमी। स्नानदानैर्बहुफला नागलोकप्रदायिनी॥" | 429 | S |
| campā-ṣaṣṭhī (Mallāri/Khaṇḍobā) | NEW `campA-SaSThI~mArgazIrSa`; yoga-variants (vaidhṛti+ravivāra; viśākhā+bhauma; śatabhiṣak+ravivāra) else paraviddhā | 09/06 | Mallāri-māhātmya "मार्गे भाद्रपदे शुक्ला षष्ठी वैधृतिसंयुता। रविवारेण संयुक्ता सा चम्पेतीह विश्रुता॥"; "मार्गशीर्षेऽमले पक्षे षष्ठ्यां वारेंऽशुमालिनः। शततारागते चन्द्रे लिङ्गं स्याद्दृष्टिगोचरम्॥" | 430 | M |
| `mitra-saptamI` | ADD SK shloka/ref | 09/07 | "तद्विष्णोर्दक्षिणं नेत्रं तदेवाकृतिमत्पुनः। अदित्यां कश्यपाज्जज्ञे मित्रो नाम दिवाकरः। सप्तम्यां तेन सा ख्याता लोकेऽस्मिन्मित्रसप्तमी॥" | 430 | S |
| mārgaśīrṣī + mṛgaśiras lavaṇa-dāna | NEW (family §6.4) | 09/15 ∧ mṛgaśiras, candrodaya | "मार्गशीर्षपौर्णमास्यां मृगशिरोयुक्तायां चूर्णितलवणस्य सुवर्णनाभं प्रस्थमेकं चन्द्रोदये ब्राह्मणाय प्रतिपादयेत्…" | 430 | M |
| `dattAtrEya~jayantI` | ADD-SH | 09/15 pradoṣa | Sahyādrikhaṇḍa "मार्गशीर्षे पञ्चदशेऽह्नि च सुनिर्मले। मृगशीर्षयुते पूर्णमास्यां बुधस्य च वासरे। जनयामास देदीप्यमानं पुत्रं सती शुभम्…" | 430 | S |
| pratyavarohaṇa (Āśvalāyana) | NEW `pratyavarOhaNam` (gRhya) | 09/14 or 09/15 sāyam | Āśv. gṛhya | 430–432 | M |

### 5.10 Pauṣa (पौषकृत्यम्, pp.432–439)

| Item | Status | Timing | Key shloka(s) | p. | Cx |
|---|---|---|---|---|---|
| `pauSa-mAsa-ArambhaH` | ADD-SH | month | MBh "पौषमासं तु कौन्तेय एकभक्तेन यः क्षिपेत्। सुभगो दर्शनीयश्च यशोभागी च जायते॥"; Vāmana "प्रासादनगरादीनि गृहप्रावरणानि च। नारायणस्य तुष्ट्यर्थं पौषे देयानि यत्नतः॥" | 432 | S |
| aṣṭakā family (`*-aSTakA-zrAddham`, `*-pUrvEdyuH`, `*-anvaSTakA-zrAddham`) | ADD-SH to all; confirm aparāhṇa-vyāpinī; confirm not held in malamāsa; add bhādra-aṣṭakā variant (Agni-smṛti) | 09/23, 10/23, 11/23, 12/23 (+ 06/23) | "अप्यनडुहो यवसमाहरेदग्निना वा कक्षमुपोषेदेषामेष्टकेति नत्वेवानष्टकः स्यात्"; "सिंहस्थे मकरस्थे वा प्रोष्ठपान्माघमासयोः। कृष्णपक्षेऽष्टका कार्या…" | 432–439 | S |
| pauṣī + puṣya alakṣmī-nāśana snāna | NEW `pauSI-puSya-snAnam` | 10/15 ∧ puṣya | Brahma "इदं जगत्पुरा लक्ष्म्या त्यक्तमासीत्ततो हरिः। पुरन्दरश्च सोमश्च तथा शुक्रबृहस्पती। पञ्चैते पुष्ययोगेन पूर्णमास्यां तपोबलात्। अलंकृतं पुनश्चक्रुः…"; "गौरसर्षपकल्केन समालिप्य स्वकां तनुम्…" | 439 | S |

### 5.11 Māgha (माघकृत्यम्, pp.439–512)

| Item | Status | Timing | Key shloka(s) | p. | Cx |
|---|---|---|---|---|---|
| māgha-snāna start | NEW `mAgha-snAna-ArambhaH` (options: 10/11 | 10/15 | 10/30 | makara-saṅkrānti) | aruṇodaya | Brahma "एकादश्यां तु शुक्लायां पौषमासे समारभेत्। द्वादश्यां पौर्णमास्यां वा शुक्लपक्षे समापनम्॥"; "अरुणोदये तु संप्राप्ते स्नानकाले विचक्षणः। माधवाङ्घ्रियुगं ध्यायन्यः स्नाति सुरपूजिते। प्रयागवारिणि शुभे तस्य पुण्यस्य का मितिः॥"; Padma "माघमासे रटन्त्यापः किंचिदभ्युदिते रवौ। ब्रह्मघ्नं वा सुरापं वा कं पतन्तं पुनीमहे॥"; "उत्तमं तु सनक्षत्रं लुप्ततारं तु मध्यमम्। सवितर्युदिते भूप ततो हीनं प्रकीर्तितम्॥"; saṅkalpa "माघमासमिमं पूर्णं स्नास्येऽहं देव माधव। तीर्थस्यास्य जले नित्यम्…"; daily "मकरस्थे रवौ माघे गोविन्दाच्युत माधव। स्नानेनानेन मे देव यथोक्तफलदो भव॥" | 439–441 | S |
| `mAgha-snAnapUrtiH` | FIX 11/30 → 11/15 (+ 11/12 variant) + ADD | – | "सवित्रे प्रसवित्रे च परं धाम जले मम। त्वत्तेजसा परिभ्रष्टं पापं यातु सहस्रधा॥ दिवाकर जगन्नाथ प्रभाकर नमोऽस्तु ते। परिपूर्णं करिष्येऽहं माघस्नानं तवाज्ञया॥" | 441, 481 | S |
| `mAgha-mAsa-ArambhaH` | ADD tila-pātra / tila dāna shlokas | month | "देवदेव जगन्नाथ वाञ्छितार्थफलप्रद। तिलपात्रं प्रदास्यामि तवाङ्गे संस्थितो ह्यहम्॥"; "तिलाः पुण्याः पवित्राश्च सर्वपापहराः स्मृताः। शुक्लाश्चैव तथा कृष्णा विष्णुगात्रसमुद्भवाः॥"; Vāmana "माघे मासि तिलाः शस्तास्तिलधेनुश्च दानतः…" | 441–442 | S |
| `ardhOdaya-puNyakAlaH`, `mahOdaya-puNyakAlaH` | ADD-SH (mahodaya has none); verify "day-only" condition in solar.py | amā ∧ vyatīpāta ∧ śravaṇa ∧ ravivāra (pauṣa/māgha) | "माघामायां व्यतीपाते आदित्ये विष्णुदैवते। अर्धोदयं तदित्याहुः सहस्रार्कग्रहैः समम्॥"; MBh "अमार्कपातश्रवणैर्युक्ता चेत्पौषमाघयोः। अर्धोदयः स विज्ञेयः कोटिसूर्यग्रहैः समः॥"; Vasiṣṭha "…किंचिन्न्यूनो महोदयः। दिवैव योगः शस्तोऽयं न तु रात्रौ कदाचन॥"; Skanda "अर्धोदये तु संप्राप्ते सर्वं गङ्गासमं जलम्…"; "सुवर्णपायसामत्रं यस्मादेतत्त्रयीमयम्। आवयोस्तारकं यस्मात्तद्गृहाण द्विजोत्तम॥" | 442–446 | S (+code check) |
| prayāga/veṇī/asthi-prakṣepa, ayuta-homa, kuṇḍa geometry | SKIP | – | – | 446–478 | – |
| guḍa-lavaṇa dāna | NEW `mAgha-guDa-lavaNa-dAnam` | 11/03 | Bhaviṣya "माघे शुक्लतृतीयायां गुडस्य लवणस्य च। दानं श्रेयस्करं राजन्स्त्रीणां च पुरुषस्य च। गुडेन तृप्यते देवी लवणेन स्वयं प्रभुः॥" | 479 | S |
| `varakunda-caturthI` | ADD SK shlokas | 11/04 | "शुक्लचतुर्थ्यां तु कुन्दपुष्पैः सदाशिवम्। संपूज्य यस्तु नक्ताशी संप्राप्नोति श्रियं नरः॥"; "माघमासे तु संप्राप्ते चतुर्थी कुन्दसंज्ञिता। उपोष्या सा सुरश्रेष्ठ ततो राज्यं भविष्यति॥" | 479 | S |
| `vasanta-zrI-paJcamI` | verify shloka | 11/05 | Purāṇasamuccaya "माघमासे नृपश्रेष्ठ शुक्लायां पञ्चमीतिथौ। रतिकामौ तु संपूज्य कर्तव्यः सुमहोत्सवः। दानानि च प्रदेयानि तेन तुष्यति माधवः॥" | 479 | – |
| `ratha-saptamI` | FIX (pūrvaviddha when both aruṇodaya) + ADD | 11/07 | "सूर्यग्रहणतुल्या तु शुक्ला माघस्य सप्तमी। अरुणोदयवेलायां तत्र स्नानं महाफलम्॥"; "कृत्वा षष्ठ्यामेकभक्तं सप्तम्यां निश्चलं जलम्। रात्र्यन्ते चालयेथास्त्वं दत्त्वा शिरसि दीपकम्…"; "नमस्ते रुद्ररूपाय रसानां पतये नमः। वरुणाय नमस्तेऽस्तु हरिवास नमोऽस्तु ते॥"; "यद्यज्जन्मकृतं पापं मया जन्मसु सप्तसु। तन्मे रोगं च शोकं च माकरी हन्तु सप्तमी॥" | 479–480 | S |
| padmaka (ravivāra + ṣaṣṭhī-saptamī) | verify `padmaka-yOgaH-2/3` definitions + ADD | 11/06–07 ∧ ravivāra, pūrvāhṇa | "रविवारेण युक्तायां सप्तम्यामुत्तरायणे। पुंनामधेयनक्षत्रे पूजयेच्च दिवाकरम्। षष्ठीसप्तमीसंयोगे वारश्चेदंशुमालिनः। योगोऽयं पद्मको नाम सहस्रार्कग्रहैः समः॥" | 480 | S |
| `bhISmASTamI` | ADD tarpaṇa/arghya shlokas (verify) | 11/08 madhyāhna | Padma "माघमासि सिताष्टम्यां सलिले भीष्मतर्पणम्। श्राद्धं च ये नराः कुर्युस्ते स्युः सन्ततिभागिनः॥"; "वैयाघ्रपद्यगोत्राय सांकृत्यप्रवराय च। गङ्गापुत्राय भीष्माय आजन्मब्रह्मचारिणे। अपुत्राय जलं दद्मि नमो भीष्माय वर्मणे॥"; "वसूनामवताराय शन्तनोरात्मजाय च। अर्घ्यं ददामि भीष्माय आबालब्रह्मचारिणे॥" | 480 | S |
| mahānandā-navamī | NEW `mahAnandA-navamI` | 11/09 | Bhaviṣya "माघमासे तु या शुक्ला नवमी लोकपूजिता। महानन्देति सा प्रोक्ता सदानन्दकरी नृणाम्। तस्यां स्नानं तथा दानं जपो होम उपोषणम्। सर्वं तदक्षयं प्रोक्तं…" | 480 | S |
| `tilapadma-dvAdazI_or_tilOtpatti` (+`bhISma-dvAdazI`, `varAha-dvAdazI`) | ADD-SH | 11/12 | Brahma "माघे तु शुक्लद्वादश्यां यतो हि भगवान्पुरा। तिलानुत्पादयामास तपः कृत्वा सुदारुणम्…" | 480–481 | S |
| `mahAzivarAtriH` | ADD-SH; document "both-days → pūrva" (Hemādri/Madanaratna) vs Mādhava; forbid amā-yuktā | 11/29 niśītha | "माघकृष्णचतुर्दश्यामादिदेवो महानिशि। शिवलिङ्गतयोद्भूतः कोटिसूर्यसमप्रभः॥"; "वर्षे वर्षे महादेवि नरो नारी पतिव्रता। शिवरात्रौ महादेवं नित्यं भक्त्या प्रपूजयेत्॥"; "अर्धरात्रादधश्चोर्ध्वं युक्ता यत्र चतुर्दशी। तत्तिथावेव कुर्वीत शिवरात्रिव्रतं व्रती॥"; "माघफाल्गुनयोर्मध्ये यावच्छिवचतुर्दशी। अनङ्गेन समायुक्ता कर्तव्या सा सदा तिथिः॥"; saṅkalpa "शिवरात्रिव्रतं ह्येतत्करिष्येऽहं महाफलम्। निर्विघ्नमस्तु मे चात्र त्वत्प्रसादाज्जगत्पते। चतुर्दश्यां निराहारो भूत्वा शंभो परेऽहनि। भोक्ष्येऽहं भुक्तिमुक्त्यर्थं शरणं मे भवेश्वर॥" | 481–486 | M |
| ravi/bhauma śivarātri | ADD Skanda shloka to existing vāra entries | 11/29 ∧ vāra | "माघकृष्णचतुर्दश्यां रविवारो यदा भवेत्। भौमो वापि भवेद्देवि कर्तव्यं व्रतमुत्तमम्। शिवयोगस्य योगो वै तद्भवेदुत्तमोत्तमम्॥" | 483 | S |
| trispṛśā śivarātri | NEW-CODE flag `trispRzA-zivarAtriH` (C6) | 13/14/30 all touch one day | "त्रयोदशी कलाप्येका मध्ये चैव चतुर्दशी। अन्ते चैव सिनीवाली त्रिस्पृशां शिवमर्चयेत्॥" | 483 | M |
| śivarātri yāma-pūjā | NEW (LOW) 4 prahara events | 11/29 night | dugdha/dadhi/ghṛta/madhu; īśāna/aghora/vāmadeva/sadyojāta | 486–511 | M |
| `mAsazivarAtriH` | ADD-SH + document start options & rule (bahu-rātri-vyāpinī; equal → pūrva) | x/29 | (Hemādri/Skanda) | 511–512 | S |
| māgha amā + dhaniṣṭhā/śatabhiṣak | ADD SK refs to `mAgha-zraviSThA-amAvAsyA`, `mAgha-zatabhiSak-amAvAsyA`; `kaliyugAdiH` ADD | 11/30 | MBh "काले धनिष्ठा यदि नाम तत्र भवेत्तु भूपाल तदा पितृभ्यः। दत्तं तिलान्नं प्रददाति तृप्तिं वर्षायुतं तत्कुलजैर्मनुष्यैः॥"; ViṣṇuP "माघासिते पञ्चदशी कदाचिदुपैति योगं यदि वारुणेन। ऋक्षेण कालः स परः पितॄणां न ह्यल्पपुण्यैर्नृप लभ्यते सदा॥" | 512 | S |

### 5.12 Phālguna (फाल्गुनकृत्यम्, pp.513–519)

| Item | Status | Timing | Key shloka(s) | p. | Cx |
|---|---|---|---|---|---|
| `phAlguna-mAsa-ArambhaH` | ADD-SH | month | "फाल्गुने व्रीहयो गावो वस्त्रं कृष्णाजिनान्वितम्। गोविन्दप्रीणनार्थाय दातव्यं पुरुषर्षभ॥" | 513 | S |
| payovrata | NEW `aditi-payOvrata-pUrvadinam` (11/30, varāha-mṛttikā) + FIX samāpana 12/12 → 12/13 (verify Bhāgavata 8.16) | 11/30 → 12/01…12/13 | "त्वं देव्यादिवराहेण रसायाः स्थानमिच्छता। उद्धृतासि नमस्तुभ्यं पाप्मानं मे प्रणाशय॥" | 513–516 | S |
| avighna-vrata | NEW `avighna-vrata-ArambhaH` | 12/04 (4 months) | Varāha "अथाविघ्नव्रतं राजन्कथयामि शृणुष्व तत्। चतुर्थ्यां फाल्गुने मासि ग्रहीतव्यं व्रतं त्विदम्। नक्ताहारेण राजेन्द्र तिलान्नं पारणं स्मृतम्…"; "दिव्योच्चशुण्डाय गजाननाय लम्बोदरायैकदन्तायुधाय। नगात्मजादेहसमुद्भवाय कुठारहस्ताय नमो वराय॥" | 516 | S |
| `hOlikA-pUrNimA` | ADD-SH + FIX (C1 + C6 fall-back chain) | 12/15 pradoṣa, bhadrā-free | "सर्वदुष्टापहो होमः सर्वरोगोपशान्तिदः। क्रियतेऽस्यां द्विजैः पार्थ तेन सा होलिका स्मृता॥"; "अस्माभिर्भयसंत्रस्तैः कृता त्वं होलिके यतः। अतस्त्वां पूजयिष्यामो भूते भूतिप्रदा भव॥"; "प्रदोषव्यापिनी ग्राह्या पूर्णिमा फाल्गुनी सदा"; "तस्यां भद्रामुखं त्यक्त्वा पूज्या होला निशामुखे"; "सार्धयामत्रयं पूर्णा द्वितीये दिवसे यदा। प्रतिपद्वर्धमाना तु तदा सा होलिका स्मृता॥"; "रात्रौ भद्रावसाने च होलिकां तत्र दीपयेत्" | 516–518 | H |
| `hOli` / dhūli-vandana | ADD-SH (none now) + NEW `dhUli-vandanam` | 12/16 paraviddhā pratipat | "चैत्रे मासि महाबाहो पुण्या प्रतिपदा परा। यस्तस्यां श्वपचं स्पृष्ट्वा स्नानं कुर्यान्नरोत्तमः…"; "वन्दितासि सुरेन्द्रेण ब्रह्मणा शंकरेण च। अतस्त्वं पाहि नो देवि भूते भूतिप्रदा भव॥" | 518–519 | S |
| `Amra-kusuma-prAshanam` | ADD-SH (none now) | 12/16 | "चूतमग्र्यं वसन्तस्य माकन्द कुसुमं तव। सचन्दनं पिबाम्यद्य सर्वकामार्थसिद्धये॥" | 519 | S |
| phālguna dolotsava | NEW `phAlguna-dOlOtsavaH` (pūrvaviddhā) | 12/15–16 | Brahma "नरो दोलागतं दृष्ट्वा गोविन्दं पुरुषोत्तमम्। फाल्गुन्यां संयतो भूत्वा गोविन्दस्य पुरं व्रजेत्॥" | 519 | S |
| kāma-mahotsava (royal) | NEW (LOW) | 12/17 | – | 519 | S |

### 5.13 Adhika-māsa (pp.520–529)

| Item | Status | Timing | Key shloka(s) | p. | Cx |
|---|---|---|---|---|---|
| `adhika-mAsa-ArambhaH` | ADD-SH | adhika month | "अधिमासे तु संप्राप्ते गुडसर्पिर्युतानि च। त्रयस्त्रिंशदपूपानि दातव्यानि दिने दिने…"; "विष्णुरूपी सहस्रांशुः सर्वपापप्रणाशनः। अपूपान्नप्रदानेन मम पापं व्यपोहतु॥"; "कुरुक्षेत्रमयो देशः कालः पर्व द्विजो हरिः। पृथ्वीसममिदं दानं गृहाण पुरुषोत्तम॥" | 524–525 | S |
| adhika/nija policy | NEW-CODE C10 (audit per festival; `adhika_maasa_handling`) | – | Kāladarśa "अग्न्याधानाध्वरापूर्वतीर्थयात्रामरेक्षणम्…"; "उपाकर्म तथोत्सर्गः…"; Kāṭhaka "यस्मिन्मासे न संक्रान्तिः संक्रान्तिद्वयमेव वा। मलमासः स विज्ञेयो…" | 525–529 | M |
| 5-year yuga names (saṃvatsara, parivatsara, idāvatsara, anuvatsara, idvatsara) + dānas | NEW (LOW) description | – | Viṣṇudharmottara "संवत्सरे तु दातॄणां तिलदानं महाफलम्। परिपूर्वे तथा दानं यवानां…" | 529 | S |

### 5.14 Saura / sāvana / bārhaspatya / nākṣatra / yoga / karaṇa (pp.531–565)

| Item | Status | Timing | Key shloka(s) | p. | Cx |
|---|---|---|---|---|---|
| all 12 `*-saGkramaNa-*-puNyakAlaH` | ADD-SH (classification + phala + per-rāśi dāna); verify night-saṅkrānti rules in code | saṅkrānti | Vasiṣṭha "झषकर्कटसंक्रान्ती द्वे उदग्दक्षिणायने। विषुवती तुलामेषौ तयोर्मध्ये ततोऽपराः। वृषवृश्चिककुम्भेषु सिंहे चैव यदा रविः। एतद्विष्णुपदं नाम विषुवादधिकं फलम्। कन्यायां मिथुने मीने धनुष्यपि रवेर्गतिः। षडशीतिमुखी प्रोक्ता षडशीतिगुणा फलैः॥"; "अयने कोटिपुण्यं च लक्षं विष्णुपदीफलम्। षडशीतिसहस्रं तु षडशीत्याः स्मृतं बुधैः॥"; "अर्वाक् षोडश विज्ञेया नाड्यः पश्चाच्च षोडश…"; "रविसंक्रमणे प्राप्ते न स्नायाद्यस्तु मानवः। सप्तजन्मनि रोगी स्यान्निर्धनश्चैव जायते॥"; per-rāśi dāna (Viśvāmitra) — see §6.6 | 531–540 | S |
| saṅkrānti names by vāra (mandā, mandākinī, dhvāṅkṣī, ghorā, mahodarī, rākṣasī, miśritā) | NEW (LOW-MED) description / computed label | – | – | 539–540 | M |
| `makara-saGkramaNa-puNyakAlaH` | ADD (tila six-fold use; ghṛta-kambala; tulā-dāna) | – | Kālikā "…तस्मिन्नेवोत्तरायणे। विधिवच्च तथाभ्यर्च्य गव्येनाज्येन भूरिणा…"; Garuḍa "प्रथमा तु घृतस्योक्ता तेजोवृद्धिकरी तुला…" | 540–541 | S |
| saṅkrānti avatāra-pūjā | NEW (12, see §6.6) | each saṅkrānti | Viṣṇudharmottara "मेषसंक्रमणे भानोः सोपवासो नरोत्तमः। पूजयेद्भार्गवं देवं…" | 552 | S (OCR gap for tulā/vṛścika/dhanus: FLAG) |
| dhānya / āyu / āśā saṅkrānti vratas | NEW (LOW-MED) | start at ayana/viṣuva | "कालात्मा सर्वभूतात्मा वेदात्मा विश्वतोमुखः…"; "सक्षीरं सुरभीजातं पीयूषसमरूपधृक्। आयुरारोग्यमैश्वर्यमतो देहि द्विजार्पितम्॥"; "आशां तेजस्करीं पृष्ठे प्रभादीप्तियशस्करीम्। आशां सर्वत्रगां देव मम देहि नमोऽस्तु ते॥" | 552–554 | M |
| śanivāra taila-dāna, ravivāra nakta | NEW (LOW, vāra) | vāra | "यो वै सूर्यदिने भक्त्या भानुं संपूज्य श्रद्धया। नक्तं करोति पुरुषः…" | 554–557 | S |
| simha-guru godāvarī puṣkara etc. | ADD SK verses to `*-puSkara-viSeSaH` (none have shlokas) | guru-rāśi | Skanda "स्थिता गोदावरीतीरे सिंहराशिगते गुरौ…" | 557–561 | S |
| guru/śukra asta, bālya/vārdhakya | ADD SK refs to existing graha entries | – | – | 559–561 | S |
| nakṣatra-devatā pūjā (27) | NEW (LOW-MED) monthly nakṣatra events; C7 rule | nakṣatra | Devī-P "अश्विन्यामश्विनाविष्ट्वा दीर्घायुर्जायते नरः…"; "उपोषितव्यं नक्षत्रं येनास्तं याति भास्करः। यत्र वा युज्यते राम निशीथः शशिना सह॥" | 561–562 | M |
| rohiṇī-vrata (yearly), puṣya-snāna (royal) | NEW (LOW) | – | "रोहिणी जन्मनक्षत्रं देवदेवस्य चक्रिणः…"; "पुष्यस्नानं महापुण्यं राज्ञां प्रोक्तं स्वयंभुवा। वत्सरे वत्सरे कुर्यात्पुष्ययुक्ते निशाकरे॥" | 562 | S |
| vyatīpāta-vrata (13 from mārgaśīrṣa), vyatīpāta-śrāddha | ADD-SH to `vyatIpAta-zrAddham`; NEW `vyatIpAta-vratam` (LOW) | yoga 17 | "नमस्तेऽस्तु व्यतीपात सूर्यसोमसुत प्रभो। यद्दानादि कृतं किंचित्तदनन्तमिहास्तु मे॥"; "अमावास्याव्यतीपातपूर्णमास्यष्टकासु च। विद्वाञ्छ्राद्धमकुर्वाणः प्रायश्चित्तीयते तु सः॥" | 563–564 | S |
| yoga-vrata (27), karaṇa-vrata | NEW (LOW) | – | Bhaviṣya / Brahmāṇḍa | 563–565 | M |
| viṣṭi/bhadrā definition | NEW-CODE C1 (reference data) | – | "चतुर्युकादशी रात्रौ शुक्ले पूर्णाष्टमी दिवा। भद्रा त्रिदशमी रात्रौ कृष्णेऽह्न्यद्रिमनौ तिथौ॥"; Nārada "मुखे पञ्च गले त्वेका वक्षस्येकादश स्मृताः। नाभौ चतस्रः षट् श्रोण्यां तिस्रः पुच्छाख्यनाडिकाः॥" | 564–565 | H |

---

## 6. Families (implement as batches with shared templates)

### 6.1 Kalpādis (Nāgarakhaṇḍa list of 30, p.87–88)
- Existing: `*-kalpAdiH` entries (brahma, varAha, sAvitrI, pralaya…). Action: cross-check all 30 against the list in §5.1; ADD the missing ones as `aparāhṇa vyaapti` śrāddha-tithi entries with the Nāgarakhaṇḍa verse as shared shloka; ADD SK ref to existing ones.

### 6.2 Damanaka-mahotsava (Caitra, pp.86–94)
- Tithi-wise deity list (ś1 brahmā, ś2 umā-śiva-agni, ś4 gaṇeśa, ś7 sūrya, ś9 durgā, ś12 viṣṇu, ś13 anaṅga, ś14 bhairava/ekavīrā, ś15 all devas); existing damanaka entries get ADD-SH; missing tithi-deity entries NEW, one TOML each sharing a common description (see §5.1).

### 6.3 Monthly navamī Durgā names (Bhaviṣya/Devī-P, "नवम्यां पक्षयोर्द्वयोः")
| Month | Name | Existing? |
|---|---|---|
| Caitra | see §5.1 (damanaka durgā 01/09) | verify |
| Vaiśākha | caṇḍikā (p.113) | NEW 02/09, 02/24 (§5.2) |
| Jyeṣṭha | brahmāṇī / umā, śveta-rūpā (p.119) | `brahmANI-pUjA` 03/09 exists: ADD-SH; add 03/24 |
| Āṣāḍha | aindrī (p.138) | exists (04/09, add 04/24) |
| Śrāvaṇa | kaumārī (p.149) | `kaumArI-pUjA` ADD-SH; 05/24 (`caNDikA-pUjA`) ADD-SH |
| Bhādrapada | nandā | `nandA~navamI` ADD-SH |
| Āśvina | mahānavamī (durgā) | exists |
| Kārtika … Phālguna | not given explicitly in the month sections read; check the Bhaviṣyottara navamī-vrata source (Hemādri) | phase 2 |
- Implement as one template, 24 entries (both pakṣas) where missing.

### 6.4 Māsa-pūrṇimā + same-nakṣatra dānas (Viṣṇu-smṛti ch. 90)
Condition: pūrṇimā ∧ eponymous nakṣatra (intersection group). Items seen in SK:
| Pūrṇimā | Nakṣatra | Dāna | p. |
|---|---|---|---|
| caitrī | citrā | vastra (citra-vastra) | ~106 |
| vaiśākhī | viśākhā | (see §5.2) | ~115 |
| jyeṣṭhī | jyeṣṭhā | chatra + upānah | ~136 |
| āṣāḍhī | pūrvāṣāḍhā | anna-pāna | 143 |
| śrāvaṇī | śravaṇa | (upākarma day; see §5.5) | – |
| āśvayujī | aśvinī | ghṛta-pātra + suvarṇa | 355 |
| kārtikī | kṛttikā | (see mahā-kārtikī) | 406 |
| mārgaśīrṣī | mṛgaśiras | lavaṇa prastha at candrodaya | 430 |
| pauṣī | puṣya | alakṣmī-nāśana snāna | 439 |
| māghī | maghā | tila | – verify |
| phālgunī | u./pū. phalgunī | – verify | – |
- One template; S complexity; ~10 entries.

### 6.5 Pavitrāropaṇa tithi-devatās (Śrāvaṇa, p.148–149)
15 entries (pratipat dhanada … pūrṇimā pitṛs) — see §5.5 shloka; plus viṣṇu (05/12), devī (05/08 | 05/14), śiva (04/15 ⇒ 05/14 etc.) pavitrāropaṇa main entries.

### 6.6 Saṅkrānti dānas and avatāra-pūjā (pp.540, 552)
| Saṅkrānti | Dāna (Viśvāmitra) | Avatāra (Viṣṇudharmottara) |
|---|---|---|
| meṣa | meṣa | bhārgava-rāma |
| vṛṣa | go | kṛṣṇa |
| mithuna | vastra, anna, pāna | bhogiśāyin (anantaśāyin) |
| karka | ghṛta-dhenu | varāha |
| siṃha | mañca + suvarṇa | nārasiṃha |
| kanyā | vastra, surabhi | aśvaśiras (hayagrīva) |
| tulā | dhānya, bīja (+ new sasya, Brahma) | **OCR gap – re-OCR p.552** |
| vṛścika | vastra, veśma | **gap** |
| dhanus | vastra, yāna | **gap** |
| makara | dāru, agni | rāma dāśarathi |
| kumbha | go, ambu, tṛṇa | yādava-nandana (bala-rāma?) |
| mīna | harmya, mālya | matsya |
- ADD dāna line + shloka to each existing saṅkramaṇa entry; avatāra-pūjā NEW (12) or merged into the same entries' description.

### 6.7 Skanda / ṣaṣṭhī family
kumāra-ṣaṣṭhī (04/06), skanda-darśana (06/06), campā-ṣaṣṭhī (06/06 yoga; 09/06), mahā-ṣaṣṭhī (08/06 vṛścika+bhauma), existing `dEvasEnA~paJcamI` & skanda-ṣaṣṭhī — share a common description block (12 names of Skanda from SK p.~221).

### 6.8 Upākarma / utsarjana family (Śrāvaṇa)
All 7 existing upākarma TOMLs + taittirīya utsarga entries get a common shloka set (§5.5); NEW: atharva, kātīya-utsarjana, ṛgveda-utsarjana (māghī), śravaṇākarma, pratyavarohaṇa (Mārga).

### 6.9 Śrāddha-season family (Mahālaya)
`mahAlaya-pakSa*`, `yati-mahAlayam`, `zastrahatacaturdazI`, `madhyASTamI`, `avidhavA-navamI`, `mahAbharaNI`, `gajacchAyA-yOgaH`, `dauhitra-pratipat` — shared shlokas + alternate start/end markers (§5.6).

---

## 7. Deferred / skipped (with reason)

| Item | Reason |
|---|---|
| Ekādaśī nirṇaya (all months), vedha rules, mahādvādaśī details beyond shlokas | Out of scope per request; already handled by dedicated code |
| General sections: tithi-sāmānya, kāla-vibhāga, śrāddha-prayoga, homa/kuṇḍa geometry (pp.446–478), vṛṣotsarga prayoga (pp.391–405), śivarātri pūjā/kathā (pp.486–511), navarātra homa (pp.314–324) | Prayoga, not calendrical |
| Kārtika udyāpanas (pp.406–424) | Vrata-udyāpana; no fixed date |
| Vaiśākha ś12 two-graha vyatīpāta (C8) | Very rare; needs new graha-yoga infra |
| Royal rites: lohābhisārika, vājinīrājana, nṛpa-nīrājana, śakradhvaja details, puṣya-snāna, kāma-mahotsava | LOW demand; add later as `royal` tag if desired |
| Janmāṣṭamī vaiṣṇava-vs-smārta full split, jayantī budha-yoga | Needs C3/C5; phase 2 |
| Mahālakṣmī doṣa rules (sun in 2nd half of hasta; tridina/avama) | Needs C2 fine-grained; phase 2 |
| Kapilā-ṣaṣṭhī sun-in-hasta clause | C2 |
| Mahājyeṣṭhī, mahā-kārtikī (guru clause) | C2 |
| 27 yoga-vratas, karaṇa-vrata | LOW value |
| Pages 614–617 (pāṭhāntara appendix) | Needs re-OCR; use only to resolve disputes |

---

## 8. Implementation order (batches, each a separate PR in adyatithi / jyotisha)

1. **Batch 0 – hygiene** (adyatithi): reference-string normalisation; wrong page refs (§3.1); OCR-fix helper list committed as `docs/smriti_kaustubha_ocr_fixes.md` (optional).
2. **Batch 1 – FIX timing, data-only** (adyatithi, no code): all §4 rows that only change `kaala`/`priority`/`anga_number`/month (madana-trayodaśī, nāga-pañcamī, śiva-śayana, kṛta/tretā-yugādi, dauhitra, zukla-dEvI-pUjA, mahālakṣmī start/end, sarasvatī-visarjana nakṣatra, snāna-pūrti ×3, ratha-saptamī, durgāṣṭamī, mahānavamī, vaṭa-pūrṇimā, kālabhairava, upāṅga-lalitā, govardhana prātaḥ). Regenerate a year of panchangas for 2–3 locations and diff against a known almanac before merging.
3. **Batch 2 – ADD-SH, month-by-month** (adyatithi): 12 small PRs (Caitra … Phālguna + saura), each touching only `shlokas`/`references_primary`/`description`. OCR-corrected per §2. Highest value per effort.
4. **Batch 3 – NEW simple** (adyatithi): plain tithi (+kaala/priority) entries — kumāra-ṣaṣṭhī, mahattama, skanda-darśana, nandotsava, kuśagrahaṇī, mārgapālī, alakṣmī-niṣkāsana, ulkā-dāna (w/o tulā clause first), guḍa-lavaṇa-dāna, mahānandā-navamī, avighna-vrata, dhūli-vandana, dolotsava, ākāśa-dīpa-ārambha, kārtika-/māgha-snāna-ārambha, tithi-devatā pavitrāropaṇa (15), monthly navamī-durgā names, kalpādis gap-fill.
5. **Batch 4 – NEW with existing intersection/vāra support**: mahā-caturthī (vāra), śrāvaṇa somavāra/bhaumavāra, budha-śravaṇa-dvādaśī, campā-ṣaṣṭhī variants, jyeṣṭhā-gaurī, nīla-jyeṣṭhā, maghā-trayodaśī, pauṣī-puṣya, masa-pūrṇimā-nakṣatra dānas (§6.4), sarasvatī-bali, mahā-kārtikī (nakṣatra only), durgā-visarjana (śravaṇa pāda), bilva-bodhana variants, mahā-ṣaṣṭhī (after verifying solar-month intersection = C9).
6. **Batch 5 – jyotisha code** (one PR per capability, with tests): C1 bhadrā segmentation → then Holikā & Rakṣābandhana FIX; C6 next-day-yāma rules → Govardhana, Holikā pratipat, trispṛśā; C3 nakṣatra override → aparājitā/sīmollaṅghana, janmāṣṭamī; C4 exclusion + solar gating → dūrvāṣṭamī; C9 → nāndīmukha, ulkā, mahā-ṣaṣṭhī; C5 → jayantī; C7 → nakṣatra vratas; C2 → mahājyeṣṭhī, kapilā, padmaka/mahā-kārtikī full; C10 adhika audit.
7. **Batch 6 – LOW**: royal rites, yoga/karaṇa vratas, saṅkrānti names, 27 nakṣatra-devatā pūjās, yuga-varṣa names.

Per-PR checklist: (a) TOML schema validates; (b) `shlokas` OCR-cleaned and cross-read against the page image where §2.4 flags it; (c) `references_primary` = "Smriti Kaustubha p.NNN"; (d) regenerate sample calendars and eyeball the new/changed dates for 3 years; (e) no duplicate ids (check alias names in `[names]`).

---

## 9. Phase 2 (not in this pass)

- **Tithi-didhiti** (json ~1–101, general tithi-nirṇaya) — mine the generic yugma/vedha tables to validate `priority` defaults per tithi across all adyatithi entries (e.g. "युग्माग्नियुगभूतानां…").
- Re-OCR list in §2.4 and the pāṭhāntara appendix; revisit shlokas marked "[?]" in this plan.
- Cross-validate against Nirṇaya-sindhu / Dharma-sindhu for items where SK records a dispute (navarātra pratipat, śivarātri both-days, janmāṣṭamī smārta/vaiṣṇava, mahālaya end).
