# Forestry and Geology syllabus map — source-cycle implementation specification

## Status and safe-use rules

This is a structured implementation map for the next catalogue increment. It is **not** a claim that the 2028 syllabus has been published or verified, and it is not a verbatim transcription of every syllabus sentence. The source-cycle syllabus must remain attached to each topic. Never merge two exam cycles or assume that IFoS and UPPSC ACF/RFO wording, paper structure, or depth are identical.

- IFoS baseline: Indian Forest Service Examination Rules, 2026, Gazette of India, Part I, Section 1, 4 February 2026. Official PDF: https://egazette.gov.in/WriteReadData/2026/269830.pdf
- UPPSC baseline: Advertisement A-1/E-1/2025, dated 20 February 2025, including Appendix 6. The accessible PDF copy is mirrored by a third party; verify against the Commission's copy before treating it as authoritative: https://uppsc.up.nic.in/Home
- UPPSC mirrored document: https://cdn-images.prepp.in/public/image/View_Enclosure_UPPSC_Notification_ce87c8a0e4cc86ea56b1eec167db36b9.pdf

## Topic hierarchy

Use the stable hierarchy `exam -> cycle -> optional subject -> paper -> section -> syllabus heading -> atomic subtopic`. Every leaf should retain:
- source_id and cycle_year;
- exact source locator (appendix/section/page);
- original heading and source wording;
- normalized concept key (for cross-exam discovery only);
- verification status;
- whether the item is a heading, subtopic, or practice outcome.

Do not overwrite existing `syllabus_nodes` IDs. New node IDs must be deterministic and exam/cycle/subject-specific, e.g. `ifos-2026-forestry-p1-a-silviculture-systems`.

## UPSC IFoS 2026 — Forestry

The Gazette places Forestry among the 14 optional subjects. It has two conventional papers. Paper I includes Sections A and B; Paper II continues the subject-specific syllabus. Seed headings from the official Gazette (Appendix I, Section III, Forestry):

### Paper I — Section A
1. Silviculture — General: ecological and physiological factors; regeneration and propagation; nursery and planting; establishment and tending.
2. Silviculture — Systems: clear-felling, shelterwood, selection, coppice and conversion systems; forest-type and plantation systems; species choice; stand establishment and management; enrichment, mechanisation, aerial seeding and thinning.
3. Silviculture — Mangrove and Cold Desert: habitat and characteristics; establishment, rehabilitation and protection of mangroves; cold-desert species identification and management.
4. Silviculture of Trees: advances in tropical silviculture and silviculture of the economically important Indian tree species listed in the Gazette.

### Paper I — Section B
1. Agroforestry, Social Forestry, Joint Forest Management and Tribology: agroforestry scope and role; agro-ecological systems; multipurpose trees and NTFPs; social/urban forestry; JFM; tribal communities and participation.
2. Forest Soils, Soil Conservation and Watershed Management: forest soil formation and properties; wind/water erosion; reclamation; soil organic matter and nutrient cycles; watershed hydrology, recharge, harvesting, slope/river/landslide management.
3. Environmental Conservation and Biodiversity: conservation principles; deforestation and development impacts; forest fire; biodiversity and protected-area related concepts. Capture remaining source headings from the complete official paper before marking this paper complete.

### Paper II
The existing IFoS Gazette contains further Forestry headings on forest management and management systems, forest protection, forest economics and legislation, and forest inventory. Import all remaining headings and subclauses from the official Paper II text before marking the paper complete. Retain original section boundaries and page references.

## UPSC IFoS 2026 — Geology

The Gazette lists Geology as an optional subject with two conventional papers.

### Paper I — Section A
1. General Geology: solar system and meteorites; earth origin/interior and age; volcanism; earthquakes and seismicity; island arcs, trenches and ridges; continental drift, sea-floor spreading and plate tectonics; isostasy, orogeny and epeirogeny.
2. Geomorphology and Remote Sensing: weathering and mass wasting; landforms, slopes and drainage; geomorphic cycles; Indian subcontinent geomorphology; aerial photographs; electromagnetic spectrum, satellites/sensors, IRS products, GIS and GPS.
3. Structural Geology: geological mapping and map reading; projection diagrams; stress/strain; rock deformation; folds, faults, foliations, lineations, joints and unconformities; superposed deformation; petrofabrics.

### Paper I — Section B
4. Palaeontology: species/nomenclature; mega- and microfossils; preservation and applications; specified fossil groups and evolutionary trends; Siwalik fauna; Gondwana flora.
5. Stratigraphy and Geology of India: stratigraphic classification; Precambrian and Phanerozoic rocks; major boundary problems; Indian palaeoclimate and palaeogeography; tectonic framework and Himalayan evolution.
6. Hydrogeology and Engineering Geology: hydrologic cycle and groundwater movement; aquifer properties; groundwater chemistry, exploration, recharge and management; rainwater harvesting; engineering properties of rocks; dams, tunnels, bridges; landslides and earthquake-resistant structures.

### Paper II
1. Mineralogy: crystal systems/symmetry; X-ray crystallography; optical mineralogy; silicate structures and common rock-forming and non-silicate minerals.
2. Igneous and Metamorphic Petrology: magma generation/crystallisation; phase diagrams and differentiation; igneous petrography/petrogenesis; metamorphic agents, grades, facies, textures, assemblages, metasomatism and Indian granulite terrains.
3. Sedimentology: sediment formation, diagenesis and lithification; clastic/non-clastic rocks; facies, provenance, structures and Indian sedimentary basins.
4. Economic Geology: ore terminology and classification; deposit-forming processes and controls; Indian metallic/industrial mineral deposits; coal and petroleum; mineral policy and conservation.
5. Mining Geology: geological/geophysical/geochemical/geobotanical prospecting; sampling and reserve estimation; exploration/mining methods; beneficiation and ore dressing.
6. Geochemistry and Environmental Geology: cosmic/planetary/earth composition; trace elements and crystal chemistry; thermodynamics; natural hazards and mitigation; mining/industrial/radioactive waste; water pollution and environmental legislation.

## UPPSC ACF/RFO 2025 — Forestry and Geology

Use the 2025 Advertisement A-1/E-1/2025 Appendix 6 as a separate source version. The ACF/RFO scheme has two optional subjects, each with two papers. Do not reuse IFoS node IDs.

- Forestry: capture Paper I and Paper II headings independently from Appendix 6. The mirrored copy shows Paper II headings including Forest Management and Management Systems; Agroforestry, Social Forestry, Joint Forest Management and Tribology; Forest Soils, Soil Conservation and Watershed Management; Environmental Conservation and Biodiversity; Forest Economics and Legislation. The full Paper I and all Paper II subclauses must be checked line-by-line before the subject is marked complete.
- Geology: Appendix 6 contains the Geology Paper I / Paper II syllabus. Capture the six Paper I headings (General Geology; Geomorphology and Remote Sensing; Structural Geology; Palaeontology; Stratigraphy and Geology of India; Hydrogeology and Engineering Geology) and six Paper II headings (Mineralogy; Igneous and Metamorphic Petrology; Sedimentology; Economic Geology; Mining Geology; Geochemistry and Environmental Geology). Preserve UPPSC-specific wording, including differences such as marine mineral resources/Law of Sea where stated.

## Cross-exam topic mapping rules

Create crosswalk records only when the underlying concepts are genuinely shared. Use relations such as:
- `same_concept_different_depth`: concept overlaps, but paper depth/assessment differs;
- `shared_foundation`: common foundation supports both syllabi;
- `exam_specific_application`: same base concept, distinct applied treatment;
- `same_source_wording`: source wording is materially identical.

Candidate shared clusters to review (not auto-equivalences):
- Forest ecology, biodiversity and conservation;
- forest types, forest resources and Indian vegetation;
- forest soils, soil properties, erosion and watershed management;
- agroforestry, social forestry and community participation;
- remote sensing/GIS applications in forestry and geology (different disciplinary outcomes);
- environmental impact, mining impacts and natural hazards;
- groundwater, hydrology and land degradation.

A crosswalk must include source and target node IDs, relation, rationale, source-cycle pair, and reviewer status. Do not automatically mark a topic complete in one exam when the user completes its mapped counterpart. Completion can be shared only after the user accepts a coverage equivalence or completes the target-specific depth/practice requirement.

## Resource mapping contract

A resource record should include title, publisher/author, resource type, URL/ISBN, language, publication/edition year, free/paid flag, official/recommended status, source checked date, and mapped syllabus node IDs. Distinguish official primary sources (Gazette, Forest Survey of India, MoEFCC, Geological Survey of India, ISRO, IMD, CPCB) from textbooks and coaching material. Never invent page numbers or claim a book covers a topic without checking the edition.

## Acceptance criteria for the application milestone

1. Forestry and Geology appear only for exams where the selected cycle permits them.
2. Candidate's saved optional selection controls which subject tree appears.
3. IFoS and ACF/RFO have separate paper/section/topic trees and source locators.
4. Topic overlap is shown as a suggestion with rationale, not silently merged.
5. Every displayed syllabus node exposes its source cycle and verification status.
6. A paper is marked `complete` only after every listed source heading and subclause is imported and checked.
7. Existing plan history and task completion are preserved during catalogue upgrades.
8. Unit tests cover duplicate seeding, cycle isolation, optional selection, crosswalk directionality and account isolation.

## Explicit limitations

This map is a build specification and partial topic outline, not a full authoritative syllabus transcription. UPPSC source hosting is mirrored; source verification remains open. The 2028 notices must be imported as new versions when officially released. Do not use this file alone to assert 2028 eligibility, exam dates, or complete syllabus coverage.
