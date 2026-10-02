# Sources and verification boundaries

Prepared 2 October 2026. All case text is newly authored; these are not official exam items or copied clinical vignettes.

## Blueprint topic source

The topic headings and checklist were directly inspected at:

- https://wizari.netlify.app/
- https://wizari.netlify.app/medicine
- https://wizari.netlify.app/surgery
- https://wizari.netlify.app/obgyn
- https://wizari.netlify.app/pediatrics

The website is a study tracker. Its ministerial authority and completeness were not independently established. Broad topics such as fractures or pituitary disorders require educational selection of specific diagnoses. A diagnosis being related to a heading does not certify that it will appear on the examination.

## Primary clinical references consulted for selected patterns

These references were used to check selected clinical patterns, not to certify every one of the 700 cases. The full bank has not undergone independent clinician review.

- Pneumonia: https://www.nhlbi.nih.gov/health/pneumonia/symptoms
- Pulmonary embolism: https://www.nhlbi.nih.gov/health/pulmonary-embolism
- VTE diagnosis: https://www.nhlbi.nih.gov/health/venous-thromboembolism/diagnosis
- Endocarditis: https://www.nhlbi.nih.gov/health/heart-inflammation/endocarditis
- Compartment syndrome: https://www.orthoinfo.org/diseases--conditions/compartment-syndrome/
- Scaphoid fracture: https://www.orthoinfo.org/diseases--conditions/scaphoid-fracture-of-the-wrist
- Distal radius fractures: https://www.orthoinfo.org/diseases--conditions/distal-radius-fractures-broken-wrist/
- Open fractures: https://www.orthoinfo.org/diseases--conditions/open-fractures/
- Ectopic pregnancy and miscarriage: https://www.nice.org.uk/guidance/ng126
- Pre-eclampsia: https://www.nhs.uk/conditions/pre-eclampsia/
- Childhood nephrotic syndrome: https://www.niddk.nih.gov/health-information/kidney-disease/children/nephrotic-syndrome-children
- Measles: https://www.cdc.gov/measles/signs-symptoms/index.html
- Pertussis: https://cdc.gov/pertussis/hcp/clinical-signs/index.html
- Diphtheria: https://www.cdc.gov/diphtheria/hcp/clinical-signs/index.html
- Sickle cell disease: https://www.nhlbi.nih.gov/health/sickle-cell-disease/symptoms
- Thalassemia: https://www.nhlbi.nih.gov/health/thalassemia/symptoms

## Technical reference

The bot calls the HTTPS Telegram Bot API directly using Python's standard library:

- https://core.telegram.org/bots/api

Relevant features: getUpdates polling, inline keyboards, callback queries, sendMessage with message_thread_id, getChatMember, setMyCommands, and deleteWebhook.

## Validation completed

Automated offline tests check clue timing and final answer window, saved scores and recovery, topic isolation, owner-only menu choices, host/admin stop rules, alias acceptance, conservative spelling tolerance, random selection, and no duplicate scoring. Tests use a fake Telegram transport and a controllable clock.

Live Telegram connectivity, BotFather setup, and real hosting were not tested because no bot token was provided. The bot is packaged for the user to connect and run. No external account was created or deployed.

## Expansion references

- NCI: https://www.cancer.gov/types/breast/breast-cancer-types/paget-disease-breast
- NIDDK: https://www.niddk.nih.gov/health-information/endocrine-diseases/multiple-endocrine-neoplasia-type-1
- RCOG: https://www.rcog.org.uk/guidance/browse-all-guidance/green-top-guidelines/ovarian-masses-in-premenopausal-women-management-of-suspected-green-top-guideline-no-62/
- NICE: https://www.nice.org.uk/guidance/NG123

Checklist inspected again on 2026-10-02. Detailed representative mappings: BLUEPRINT_AUDIT.md and data/blueprint_topic_crosswalk.json. References validate selected patterns, not every newly authored case.
