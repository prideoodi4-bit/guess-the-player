"""Explicit topic-to-case crosswalk based on the inspected website checklist.
Mappings are representative clinical examples, not proof of exhaustive curricular coverage.
"""
import json
from pathlib import Path
from engine import normalize,SPECIALTIES
ROOT=Path(__file__).resolve().parent
# specialty|section|exact displayed topic (group children retained)|case-name fragments separated by ;
# A dash marks a curricular item that cannot be covered by diagnosis guessing alone.
ROWS='''
medicine|Cardiovascular System (CVS)|Cardiac arrest & cardiopulmonary resuscitation|Ventricular fibrillation
medicine|Cardiovascular System (CVS)|Hypertension & Hypertensive Emergency, Aortic dissection|Hypertensive emergency;Acute aortic dissection
medicine|Cardiovascular System (CVS)|Acute coronary syndrome — STEMI, NSTEMI, unstable angina|ST elevation myocardial infarction;Non ST elevation myocardial infarction;Unstable angina
medicine|Cardiovascular System (CVS)|Heart failure (systolic & diastolic), acute pulmonary edema|Heart failure with reduced ejection fraction;Heart failure with preserved ejection fraction;Acute pulmonary edema
medicine|Cardiovascular System (CVS)|Cardiac tamponade & pericardial diseases|Cardiac tamponade;Acute pericarditis
medicine|Cardiovascular System (CVS)|Atrial fibrillation|Atrial fibrillation
medicine|Cardiovascular System (CVS)|Supraventricular tachycardia|Supraventricular tachycardia
medicine|Cardiovascular System (CVS)|Rheumatic fever, Valvular heart disease, Infective endocarditis|Acute rheumatic fever;Mitral stenosis;Aortic stenosis;Infective endocarditis
medicine|Cardiovascular System (CVS)|Congenital heart disease — VSD, ASD, TOF, PDA|Ventricular septal defect;Atrial septal defect;Tetralogy of Fallot;Patent ductus arteriosus
medicine|Cardiovascular System (CVS)|Cardiomyopathy|Dilated cardiomyopathy;Hypertrophic cardiomyopathy
medicine|Cardiovascular System (CVS)|Primary & secondary prevention of cardiovascular diseases|-
medicine|Respiratory System|Asthma & allergic bronchitis|Asthma
medicine|Respiratory System|Acute upper respiratory tract infection|Acute viral upper respiratory tract infection
medicine|Respiratory System|Pneumonias — lower respiratory tract infections|Community acquired pneumonia;Pneumocystis jirovecii pneumonia
medicine|Respiratory System|Suppurative lung disease & Bronchiectasis|Lung abscess;Bronchiectasis
medicine|Respiratory System|Pulmonary tuberculosis|Pulmonary tuberculosis
medicine|Respiratory System|Respiratory failure|Acute hypercapnic respiratory failure;Acute hypoxemic respiratory failure
medicine|Respiratory System|Pleural disease — effusion, pneumothorax|Pleural effusion;Spontaneous pneumothorax
medicine|Respiratory System|Lung cancer|Lung cancer
medicine|Respiratory System|Acute pulmonary embolism|Pulmonary embolism
medicine|Respiratory System|Chronic bronchitis & emphysema|Chronic obstructive pulmonary disease;Alpha 1 antitrypsin deficiency
medicine|Respiratory System|Interstitial lung disease|Idiopathic pulmonary fibrosis
medicine|Respiratory System|Adult respiratory distress syndrome — ARDS|Acute respiratory distress syndrome
medicine|Gastroenterology & Hepatology|Oesophagitis & GERD|Gastroesophageal reflux disease
medicine|Gastroenterology & Hepatology|Gastritis & Peptic ulcer|Peptic ulcer disease
medicine|Gastroenterology & Hepatology|GIT bleeding|Esophageal variceal bleeding;Peptic ulcer disease
medicine|Gastroenterology & Hepatology|Malabsorption|Celiac disease
medicine|Gastroenterology & Hepatology|Chronic inflammatory bowel disease|Crohn disease;Ulcerative colitis
medicine|Gastroenterology & Hepatology|Irritable bowel syndrome|Irritable bowel syndrome
medicine|Gastroenterology & Hepatology|Viral hepatitis, acute fulminant hepatic failure|Acute hepatitis A;Chronic hepatitis B;Chronic hepatitis C
medicine|Gastroenterology & Hepatology|Fatty liver, NAFLD|Metabolic dysfunction associated steatotic liver disease
medicine|Gastroenterology & Hepatology|Chronic liver disease — cirrhosis, portal hypertension|Liver cirrhosis;Esophageal variceal bleeding;Hepatic encephalopathy
medicine|Gastroenterology & Hepatology|Drug-induced liver disease|Drug induced liver injury
medicine|Gastroenterology & Hepatology|Acute & chronic pancreatitis|Acute pancreatitis;Chronic pancreatitis
medicine|Gastroenterology & Hepatology|Autoimmune hepatitis|Autoimmune hepatitis
medicine|Gastroenterology & Hepatology|Metabolic liver disease — Wilson’s, α1-antitrypsin, Hemochromatosis|Wilson disease;Alpha 1 antitrypsin deficiency;Hereditary hemochromatosis
medicine|Hematology & Oncology|Aplastic anemia|Aplastic anemia
medicine|Hematology & Oncology|Anemia of chronic disease|Anemia of chronic disease
medicine|Hematology & Oncology|Iron deficiency anemia|Iron deficiency anemia
medicine|Hematology & Oncology|Autoimmune hemolytic anemia|Autoimmune hemolytic anemia
medicine|Hematology & Oncology|Hemoglobinopathies — Thalassemia, Sickle cell, G6PD|Beta thalassemia trait;Sickle cell disease;G6PD deficiency
medicine|Hematology & Oncology|Acute leukemia|Acute myeloid leukemia
medicine|Hematology & Oncology|Bleeding disorders — Hemophilia, Von Willebrand, ITP|Hemophilia A;Von Willebrand disease;Immune thrombocytopenia
medicine|Hematology & Oncology|Chronic leukemia|Chronic myeloid leukemia;Chronic lymphocytic leukemia
medicine|Hematology & Oncology|Megaloblastic anemia|Megaloblastic anemia
medicine|Hematology & Oncology|Myelodysplastic syndrome|Myelodysplastic syndrome
medicine|Hematology & Oncology|Lymphomas — Hodgkin, Non-Hodgkin|Hodgkin lymphoma;Non Hodgkin lymphoma
medicine|Hematology & Oncology|Bone marrow transplantation|Graft versus host disease
medicine|Hematology & Oncology|Tumor lysis syndrome, Hypercalcemia|Tumor lysis syndrome;Hypercalcemia of malignancy
medicine|Hematology & Oncology|Multiple myeloma|Multiple myeloma
medicine|Hematology & Oncology|Blood transfusion & complications|Acute hemolytic transfusion reaction
medicine|Hematology & Oncology|Polycythemias, Essential thrombocythemia|Polycythemia vera;Essential thrombocythemia
medicine|Endocrinology & Diabetes Mellitus|Hyperthyroidism|Graves disease;Thyroid storm
medicine|Endocrinology & Diabetes Mellitus|Hypothyroidism & thyroiditis|Hashimoto thyroiditis;Subacute thyroiditis
medicine|Endocrinology & Diabetes Mellitus|Pituitary gland disorders|Acromegaly;Central diabetes insipidus
medicine|Endocrinology & Diabetes Mellitus|Adrenal insufficiency & hyperfunction|Primary adrenal insufficiency;Cushing syndrome;Primary aldosteronism;Pheochromocytoma
medicine|Endocrinology & Diabetes Mellitus|Hyperparathyroidism, Hypoparathyroidism & tetany|Primary hyperparathyroidism;Hypoparathyroidism
medicine|Endocrinology & Diabetes Mellitus|Hyperlipidemia|Familial hypercholesterolemia
medicine|Endocrinology & Diabetes Mellitus|Diabetes Mellitus — acute, chronic complications|Diabetic ketoacidosis;Hyperosmolar hyperglycemic state;Diabetic retinopathy;Diabetic kidney disease;Hypoglycemia
medicine|Endocrinology & Diabetes Mellitus|Osteoporosis, Osteomalacia, Vitamin D deficiency|Osteoporosis;Osteomalacia
medicine|Endocrinology & Diabetes Mellitus|Hypogonadism, Hirsutism & Male infertility|Primary hypogonadism
medicine|Endocrinology & Diabetes Mellitus|Malnutrition, Obesity, Mineral deficiencies|-
medicine|Neurology|Cranial nerve palsies — 1–12|Bell palsy;Third nerve palsy;Fourth nerve palsy;Sixth nerve palsy
medicine|Neurology|Seizures & Status epilepticus|Focal epilepsy;Convulsive status epilepticus
medicine|Neurology|Demyelinating diseases — multiple sclerosis|Multiple sclerosis
medicine|Neurology|Cerebrovascular accident — ischemic, hemorrhagic|Ischemic stroke;Intracerebral hemorrhage;Subarachnoid hemorrhage
medicine|Neurology|Spinal cord diseases — transverse myelitis|Transverse myelitis
medicine|Neurology|Migraine, Headache, Idiopathic intracranial hypertension|Migraine;Idiopathic intracranial hypertension
medicine|Neurology|CNS infections — meningitis, encephalitis|Bacterial meningitis;Herpes simplex encephalitis
medicine|Neurology|Peripheral neuropathy — diabetic, post-infective|Diabetic peripheral neuropathy;Guillain Barre syndrome
medicine|Neurology|Extrapyramidal disorders — Parkinsonism|Parkinson disease
medicine|Neurology|Degenerative diseases — motor neuron disease|Amyotrophic lateral sclerosis
medicine|Nephrology (~10 Qs)|Nephrotic syndrome|Nephrotic syndrome
medicine|Nephrology (~10 Qs)|Acute renal failure|Acute tubular necrosis;Acute interstitial nephritis
medicine|Nephrology (~10 Qs)|Renal dialysis — CAPD|Peritoneal dialysis associated peritonitis
medicine|Nephrology (~10 Qs)|Kidney transplantation|Acute kidney transplant rejection
medicine|Nephrology (~10 Qs)|Glomerulonephritis|IgA nephropathy;Poststreptococcal glomerulonephritis
medicine|Nephrology (~10 Qs)|Chronic renal failure|Chronic kidney disease
medicine|Nephrology (~10 Qs)|Electrolyte disturbances, water balance & blood gases|Hyperkalemia;Hypokalemia;Hypernatremic dehydration;Syndrome of inappropriate antidiuresis
medicine|Nephrology (~10 Qs)|Systemic disease & the kidney|Lupus nephritis;Diabetic kidney disease
medicine|Nephrology (~10 Qs)|Urinary tract infection|Acute pyelonephritis
medicine|Nephrology (~10 Qs)|Drug-induced nephropathy|Acute interstitial nephritis
medicine|Infectious Diseases (~10 Qs)|Infectious mononucleosis|Infectious mononucleosis
medicine|Infectious Diseases (~10 Qs)|Malaria, Leishmaniasis, Toxoplasmosis, Hydatid disease|Malaria;Visceral leishmaniasis;Cerebral toxoplasmosis;Hydatid disease
medicine|Infectious Diseases (~10 Qs)|Exanthematous febrile illness — Measles, Mumps, Herpes|Measles;Mumps;Herpes zoster
medicine|Infectious Diseases (~10 Qs)|HIV infection|HIV infection
medicine|Infectious Diseases (~10 Qs)|Brucellosis & Salmonellosis|Brucellosis;Typhoid fever
medicine|Infectious Diseases (~10 Qs)|Food poisoning & acute diarrheal diseases|Staphylococcal food poisoning
medicine|Infectious Diseases (~10 Qs)|Amoebiasis, Giardiasis & Helminthic infections|Amoebic colitis;Amoebic liver abscess;Giardiasis;Ascariasis;Hookworm infection;Strongyloidiasis
medicine|Infectious Diseases (~10 Qs)|Viral hemorrhagic fever|Crimean Congo hemorrhagic fever
medicine|Infectious Diseases (~10 Qs)|Tetanus & Rabies, Staphylococcal/streptococcal infections|Tetanus;Rabies;Staphylococcal food poisoning
medicine|Infectious Diseases (~10 Qs)|SIRS & Septic shock|Septic shock
medicine|Infectious Diseases (~10 Qs)|Fever of unknown origin|-
medicine|Rheumatology (~8 Qs)|Degenerative arthritis, Spondyloarthritis, Osteoarthritis|Osteoarthritis;Ankylosing spondylitis;Reactive arthritis
medicine|Rheumatology (~8 Qs)|Crystal arthropathy — Gout, CPPD|Gout;Calcium pyrophosphate deposition disease
medicine|Rheumatology (~8 Qs)|Metabolic bone diseases|Paget disease of bone;Osteomalacia
medicine|Rheumatology (~8 Qs)|Rheumatoid arthritis|Rheumatoid arthritis
medicine|Rheumatology (~8 Qs)|Systemic lupus erythematosus|Systemic lupus erythematosus
medicine|Rheumatology (~8 Qs)|Scleroderma|Systemic sclerosis
medicine|Rheumatology (~8 Qs)|Vasculitis|Granulomatosis with polyangiitis
medicine|Rheumatology (~8 Qs)|Dermatomyositis, Polymyositis, Behçet’s disease|Dermatomyositis;Polymyositis;Behcet disease
medicine|Rheumatology (~8 Qs)|Sjögren’s syndrome|Sjogren syndrome
medicine|Dermatology (~2 Qs)|Psoriasis|Psoriasis
medicine|Dermatology (~2 Qs)|Urticaria & Erythema|Urticaria;Erythema nodosum
medicine|Dermatology (~2 Qs)|Sexually transmitted diseases|Secondary syphilis;Genital herpes
medicine|Psychiatry (~2 Qs)|Mood disorders|Major depressive disorder;Bipolar I disorder
medicine|Psychiatry (~2 Qs)|Schizophrenia|Schizophrenia
medicine|Psychiatry (~2 Qs)|Psychosomatic disorders|Somatic symptom disorder
surgery|Basic Surgical Principles|Metabolic response to injury|-
surgery|Basic Surgical Principles|Shock, hemorrhage & transfusion|Hypovolemic shock;Septic shock;Anaphylactic shock
surgery|Basic Surgical Principles|Wound healing & tissue repair|Wound dehiscence
surgery|Basic Surgical Principles|Surgical infection & tropical infections|Surgical site infection;Necrotizing fasciitis
surgery|Basic Surgical Principles|Basic surgical skills|-
surgery|Basic Surgical Principles|Minimal access surgery|-
surgery|Basic Surgical Principles|Oncology principles|-
surgery|Basic Surgical Principles|Tissue & molecular diagnosis|-
surgery|Basic Surgical Principles|Ethics & patient safety|-
surgery|General Pediatrics|Pediatric surgical pathologies|Hypertrophic pyloric stenosis;Intussusception;Hirschsprung disease;Esophageal atresia with tracheoesophageal fistula;Congenital diaphragmatic hernia;Malrotation with midgut volvulus;Duodenal atresia;Omphalocele;Gastroschisis
surgery|General Pediatrics|Pediatric trauma|Supracondylar humerus fracture;Splenic rupture
surgery|Peri-operative Care|Care of high-risk patients|Anastomotic leak;Postoperative pulmonary embolism
surgery|Peri-operative Care|Day-case surgery|-
surgery|Peri-operative Care|Nutrition & fluid therapy|Refeeding syndrome
surgery|Abdominal Wall, Hernia & Umbilicus|Hernias — types, anatomy, repair|Indirect inguinal hernia;Direct inguinal hernia;Femoral hernia;Incisional hernia;Umbilical hernia;Obturator hernia;Spigelian hernia;Richter hernia;Strangulated hernia
surgery|Abdominal Wall, Hernia & Umbilicus|Umbilical/abdominal infections & tumors|Patent urachus
surgery|Diabetic Foot, Ulcer, Sinus, Fistula, Cyst|Diabetic foot — classification, management|Neuropathic diabetic foot ulcer;Charcot neuroarthropathy
surgery|Diabetic Foot, Ulcer, Sinus, Fistula, Cyst|Ulcers — types, causes, management|Arterial ulcer;Venous ulcer;Neuropathic diabetic foot ulcer
surgery|Diabetic Foot, Ulcer, Sinus, Fistula, Cyst|Sinuses, Fistulas, Cysts — classification, management|Pilonidal sinus;Anal fistula;Epidermoid cyst
surgery|Gastrointestinal Tract (GIT)|Abdominal history & examination|-
surgery|Gastrointestinal Tract (GIT)|GI endoscopy|-
surgery|Gastrointestinal Tract (GIT)|Peritoneum, Mesentery, Retroperitoneum|Acute mesenteric ischemia;Perforated peptic ulcer
surgery|Gastrointestinal Tract (GIT)|Esophagus, Stomach, Duodenum|Esophageal achalasia;Esophageal cancer;Gastric cancer;Gastrointestinal stromal tumor;Mallory Weiss tear;Boerhaave syndrome;Gastric outlet obstruction
surgery|Gastrointestinal Tract (GIT)|Bariatric & metabolic surgery|Early dumping syndrome;Late dumping syndrome
surgery|Gastrointestinal Tract (GIT)|Liver, Spleen, Gall bladder, Bile ducts|Hepatocellular carcinoma;Cholangiocarcinoma;Splenic rupture;Biliary colic;Acute cholecystitis;Acute acalculous cholecystitis;Acute cholangitis;Choledocholithiasis;Mirizzi syndrome;Post cholecystectomy bile leak;Post splenectomy sepsis
surgery|Gastrointestinal Tract (GIT)|Pancreas, Small & Large intestine|Pancreatic adenocarcinoma;Pancreatic pseudocyst;Walled off pancreatic necrosis;Insulinoma;Gastrinoma;VIPoma;Glucagonoma;Meckel diverticulum;Acute diverticulitis;Colorectal cancer
surgery|Gastrointestinal Tract (GIT)|Inflammatory bowel disease, Functional disorders|Toxic megacolon
surgery|Gastrointestinal Tract (GIT)|Appendix, Rectum, Anus & Anal canal|Acute appendicitis;Rectal prolapse;Anal fissure;Hemorrhoids;Perianal abscess;Anal fistula
surgery|Gastrointestinal Tract (GIT)|Intestinal obstruction|Adhesive small bowel obstruction;Sigmoid volvulus;Gallstone ileus
surgery|ATLS Principles|Primary survey|Tension pneumothorax;Massive hemothorax;Hypovolemic shock;Neurogenic shock
surgery|ATLS Principles|Secondary survey|Traumatic diaphragmatic rupture;Renal trauma;Pelvic ring fracture
surgery|Breast|Inflammatory conditions|Lactational mastitis;Breast abscess;Duct ectasia
surgery|Breast|Nipple & areola disorders|Paget disease of the breast;Intraductal papilloma;Duct ectasia
surgery|Breast|Breast lumps & tumors|Fibroadenoma;Breast carcinoma;Phyllodes tumor;Fat necrosis of the breast;Fibrocystic breast changes;Inflammatory breast carcinoma;Gynecomastia;Ductal carcinoma in situ;Simple breast cyst
surgery|Thyroid & Endocrine Surgery|Thyroid anatomy & investigations|-
surgery|Thyroid & Endocrine Surgery|Hyperthyroidism & Hypothyroidism|Graves disease;Toxic multinodular goiter;Hashimoto thyroiditis
surgery|Thyroid & Endocrine Surgery|Inflammatory thyroid diseases|Hashimoto thyroiditis;Subacute thyroiditis
surgery|Thyroid & Endocrine Surgery|Goiter & Neck masses|Toxic multinodular goiter;Graves disease;Thyroglossal duct cyst
surgery|Thyroid & Endocrine Surgery|Thyroid nodules — benign/malignant|Papillary thyroid carcinoma;Follicular thyroid carcinoma;Medullary thyroid carcinoma;Anaplastic thyroid carcinoma
surgery|Thyroid & Endocrine Surgery|Post-thyroid surgery emergencies|Post thyroidectomy neck hematoma;Post thyroidectomy hypocalcemia;Recurrent laryngeal nerve injury
surgery|Thyroid & Endocrine Surgery|Parathyroid & adrenal surgery|Primary hyperparathyroidism;Pheochromocytoma
surgery|Thyroid & Endocrine Surgery|MEN syndromes|Multiple endocrine neoplasia type 1;Multiple endocrine neoplasia type 2A;Multiple endocrine neoplasia type 2B
surgery|Head & Neck|Cervical lymphadenopathy|Cervical tuberculous lymphadenitis;Metastatic cervical lymphadenopathy
surgery|Head & Neck|Salivary gland disorders|Pleomorphic adenoma;Warthin tumor;Sialolithiasis;Acute bacterial sialadenitis;Malignant parotid tumor
surgery|Head & Neck|Congenital cysts, Pharyngeal pouch|Thyroglossal duct cyst;Branchial cleft cyst;Cystic hygroma;Pharyngeal pouch
surgery|Orthopedics|Polytrauma approach|Pelvic ring fracture;Femoral shaft fracture
surgery|Orthopedics|Fracture classification|Femoral neck fracture;Intertrochanteric fracture
surgery|Orthopedics|Complications of fractures — local/systemic|Acute compartment syndrome;Fat embolism syndrome;Fracture nonunion;Avascular necrosis of the femoral head;Complex regional pain syndrome
surgery|Orthopedics|Shoulder, Humerus, Elbow, Radius/Ulna, Wrist/Hand fractures|Clavicle fracture;Humeral shaft fracture;Supracondylar humerus fracture;Radial head fracture;Colles fracture;Smith fracture;Scaphoid fracture;Monteggia fracture dislocation;Galeazzi fracture dislocation
surgery|Orthopedics|Spine, Pelvis, Hip/Acetabulum, Femur fractures|Vertebral compression fracture;Pelvic ring fracture;Femoral neck fracture;Intertrochanteric fracture;Femoral shaft fracture;Posterior hip dislocation
surgery|Orthopedics|Knee, Tibia/Fibula, Ankle/Foot fractures|Tibial plateau fracture;Tibial shaft fracture;Patellar fracture;Lateral malleolus fracture;Calcaneal fracture;Jones fracture;Lisfranc injury
surgery|Orthopedics|Nerve injuries|Radial nerve palsy;Carpal tunnel syndrome
surgery|Orthopedics|Bone & joint infections — acute/chronic|Osteomyelitis;Septic arthritis
surgery|Orthopedics|Genetic & metabolic bone disorders, Neuromuscular disorders|Osteogenesis imperfecta
surgery|Orthopedics|Bone/joint tumors — benign/malignant|Osteochondroma;Osteosarcoma;Ewing sarcoma
surgery|Orthopedics|Non-traumatic disorders: Shoulder|Adhesive capsulitis;Rotator cuff tear
surgery|Orthopedics|Non-traumatic disorders: Elbow/Wrist/Hand|Lateral epicondylitis;De Quervain tenosynovitis;Trigger finger;Carpal tunnel syndrome
surgery|Orthopedics|Non-traumatic disorders: Hip|Developmental dysplasia of the hip;Slipped capital femoral epiphysis;Legg Calve Perthes disease;Avascular necrosis of the femoral head
surgery|Orthopedics|Non-traumatic disorders: Knee|Baker cyst;Meniscal tear;Anterior cruciate ligament tear
surgery|Orthopedics|Non-traumatic disorders: Ankle/Foot|Charcot neuroarthropathy
surgery|Orthopedics|Non-traumatic disorders: Neck/Spine|Lumbar disc herniation;Cauda equina syndrome
surgery|Urology|Urolithiasis|Ureteric calculus
surgery|Urology|Uro-oncology|Prostate cancer;Bladder cancer;Renal cell carcinoma;Testicular seminoma
surgery|Urology|BPH & LUTS|Benign prostatic hyperplasia;Acute urinary retention;Urethral stricture
surgery|Urology|Urinary tract infections/inflammation|Acute bacterial prostatitis;Epididymo orchitis
surgery|Urology|Trauma & emergencies|Testicular torsion;Ischemic priapism;Urethral injury;Bladder rupture;Renal trauma
surgery|Urology|Congenital anomalies|Posterior urethral valves;Ureteropelvic junction obstruction;Hypospadias;Undescended testis;Vesicoureteral reflux
surgery|Urology|Male infertility|Nonobstructive azoospermia;Obstructive azoospermia;Varicocele
surgery|Urology|Erectile dysfunction|Erectile dysfunction;Peyronie disease
surgery|Urology|Benign scrotal conditions|Hydrocele;Varicocele
surgery|Urology|Neurogenic bladder, Incontinence, Instruments|Neurogenic bladder;Overflow incontinence
surgery|Cardiothoracic & Vascular|Trauma & emergencies|Flail chest;Tension pneumothorax;Massive hemothorax;Ruptured abdominal aortic aneurysm
surgery|Cardiothoracic & Vascular|Arterial disorders|Peripheral arterial disease;Acute limb ischemia;Abdominal aortic aneurysm;Arteriovenous fistula
surgery|Cardiothoracic & Vascular|Venous disorders|Deep vein thrombosis;Varicose veins;Superficial thrombophlebitis
surgery|Cardiothoracic & Vascular|Lymphatic disorders & tumors|Lymphedema;Chylothorax
surgery|Cardiothoracic & Vascular|Cardiothoracic anatomy/disorders/instruments|Empyema
surgery|Radiology|Head & neck imaging|Extradural hematoma;Subdural hematoma;Meningioma
surgery|Radiology|Chest imaging|Tension pneumothorax;Massive hemothorax;Empyema
surgery|Radiology|Abdomino-pelvic imaging|Acute appendicitis;Sigmoid volvulus;Hepatocellular carcinoma
surgery|Radiology|Urinary tract imaging|Ureteric calculus;Renal cell carcinoma;Bladder rupture
surgery|Radiology|Bones/joints imaging|Colles fracture;Scaphoid fracture;Femoral neck fracture
surgery|Radiology|Vascular imaging, safety, interventional radiology|Deep vein thrombosis;Acute limb ischemia;Abdominal aortic aneurysm
surgery|Neurosurgery|CNS trauma, intracranial bleeding, GCS|Extradural hematoma;Subdural hematoma;Diffuse axonal injury
surgery|Neurosurgery|Hydrocephalus, Spina bifida|Hydrocephalus;Myelomeningocele
surgery|Neurosurgery|CNS infections|Brain abscess
surgery|Neurosurgery|CNS tumors|Meningioma;Glioblastoma;Vestibular schwannoma
surgery|Anesthesia|Types, indications & complications|Malignant hyperthermia;Local anesthetic systemic toxicity;Post dural puncture headache;High spinal block;Aspiration pneumonitis
surgery|Anesthesia|Principles of critical care in surgical patients|Septic shock;Refeeding syndrome
surgery|Plastic & Reconstructive|Burns & skin grafts|Full thickness burn;Partial thickness burn;Inhalation injury
surgery|Plastic & Reconstructive|Skin lesions (benign/malignant), Bed sores|Basal cell carcinoma;Cutaneous squamous cell carcinoma;Melanoma;Pressure ulcer
surgery|Plastic & Reconstructive|Cleft lip & palate|Cleft palate
surgery|ENT|ENT infections or emergencies/trauma|Acute otitis media;Otitis externa;Mastoiditis;Cholesteatoma;Peritonsillar abscess;Epistaxis;Septal hematoma
surgery|ENT|Audiology|Sudden sensorineural hearing loss;Vestibular schwannoma
surgery|Ophthalmology|Painful/red eye disorders|Acute angle closure glaucoma;Anterior uveitis;Corneal ulcer;Orbital cellulitis
surgery|Ophthalmology|Visual loss/blurred vision|Retinal detachment;Central retinal artery occlusion;Central retinal vein occlusion;Cataract
obgyn|Obstetrics|Physiological changes in pregnancy|-
obgyn|Obstetrics|Anatomy and embryology|-
obgyn|Obstetrics|Diabetes Mellitus in pregnancy|Gestational diabetes mellitus
obgyn|Obstetrics|Hypertensive disorder in pregnancy|Chronic hypertension in pregnancy;Gestational hypertension;Pre eclampsia;Superimposed pre eclampsia;Eclampsia;HELLP syndrome
obgyn|Obstetrics|Kidney disease & UTI in pregnancy|Acute pyelonephritis in pregnancy;Acute cystitis in pregnancy;Asymptomatic bacteriuria in pregnancy;Pregnancy related acute kidney injury;Renal cortical necrosis
obgyn|Obstetrics|Heart disease in pregnancy|Peripartum cardiomyopathy;Mitral stenosis in pregnancy
obgyn|Obstetrics|GIT problems in pregnancy|Hyperemesis gravidarum;Acute fatty liver of pregnancy;Intrahepatic cholestasis of pregnancy
obgyn|Obstetrics|Bleeding disorders in pregnancy|Maternal immune thrombocytopenia;Gestational thrombocytopenia
obgyn|Obstetrics|Coagulation disorders in pregnancy|Disseminated intravascular coagulation;Deep vein thrombosis in pregnancy;Pulmonary embolism in pregnancy;Antiphospholipid syndrome
obgyn|Obstetrics|Anemia in pregnancy|Iron deficiency anemia in pregnancy;Folate deficiency anemia in pregnancy;Vitamin B12 deficiency in pregnancy
obgyn|Obstetrics|Rh isoimmunisation|Rh alloimmunization;Hemolytic disease of the fetus and newborn
obgyn|Obstetrics|Congenital & chromosomal abnormalities|Down syndrome;Fetal hydrops
obgyn|Obstetrics|Intrauterine infection|Intraamniotic infection;Congenital cytomegalovirus infection;Congenital toxoplasmosis;Congenital rubella syndrome
obgyn|Obstetrics|IUGR & IUFD|Fetal growth restriction;Intrauterine fetal death
obgyn|Obstetrics|Labour|Shoulder dystocia;Umbilical cord prolapse
obgyn|Obstetrics|Abnormal labour|Obstructed labor;Persistent occiput posterior position;Uterine rupture
obgyn|Obstetrics|Antepartum haemorrhage — APH|Placenta previa;Placental abruption;Vasa previa
obgyn|Obstetrics|Postpartum haemorrhage — PPH|Uterine atony;Retained placental tissue;Uterine inversion;Placenta accreta spectrum;Vulvovaginal hematoma
obgyn|Obstetrics|Malpresentation|Face presentation;Brow presentation;Transverse lie
obgyn|Obstetrics|Breech|Breech presentation
obgyn|Obstetrics|Multiple pregnancy|Twin to twin transfusion syndrome
obgyn|Obstetrics|Fetal heart monitoring|Cord compression
obgyn|Obstetrics|Induction of labour|Uterine tachysystole
obgyn|Obstetrics|Preterm labour & PROM|Preterm labor;Preterm prelabor rupture of membranes;Term prelabor rupture of membranes
obgyn|Obstetrics|Prolonged pregnancy|Post term pregnancy
obgyn|Obstetrics|Puerperium|Postpartum endometritis;Puerperal sepsis;Postpartum urinary retention;Sheehan syndrome;Postpartum depression;Postpartum psychosis
obgyn|Obstetrics|Neonatal care|Hemolytic disease of the fetus and newborn
obgyn|Gynaecology|Physiology of female reproductive tract & menstrual cycle|-
obgyn|Gynaecology|Anatomy|-
obgyn|Gynaecology|Intersex|Complete androgen insensitivity syndrome;Congenital adrenal hyperplasia
obgyn|Gynaecology|Genital tract congenital abnormalities|Mullerian agenesis;Transverse vaginal septum;Imperforate hymen
obgyn|Gynaecology|Primary amenorrhea|Turner syndrome;Mullerian agenesis;Complete androgen insensitivity syndrome;Imperforate hymen
obgyn|Gynaecology|Ectopic pregnancy|Ectopic pregnancy;Ruptured ectopic pregnancy;Cervical ectopic pregnancy;Interstitial ectopic pregnancy
obgyn|Gynaecology|Miscarriage|Threatened miscarriage;Incomplete miscarriage;Complete miscarriage;Inevitable miscarriage;Missed miscarriage;Septic miscarriage
obgyn|Gynaecology|Gestational trophoblastic disease|Complete hydatidiform mole;Partial hydatidiform mole;Gestational choriocarcinoma
obgyn|Gynaecology|Puberty|Central precocious puberty;Delayed puberty
obgyn|Gynaecology|Abnormal uterine bleeding|Anovulatory abnormal uterine bleeding;Endometrial polyp;Uterine fibroid;Cervical polyp
obgyn|Gynaecology|Secondary amenorrhea|Functional hypothalamic amenorrhea;Hyperprolactinemia;Prolactinoma;Asherman syndrome;Premature ovarian insufficiency
obgyn|Gynaecology|Endometriosis & adenomyosis|Endometriosis;Adenomyosis;Ovarian endometrioma
obgyn|Gynaecology|Contraception|Contraceptive associated venous thromboembolism;Intrauterine device perforation
obgyn|Gynaecology|PCOS, hirsutism & virilization|Polycystic ovary syndrome;Congenital adrenal hyperplasia;Sertoli Leydig cell tumor
obgyn|Gynaecology|Menopause & postmenopausal bleeding|Menopause;Genitourinary syndrome of menopause;Endometrial carcinoma
obgyn|Gynaecology|Urinary incontinence|Stress urinary incontinence;Urge urinary incontinence;Mixed urinary incontinence;Vesicovaginal fistula
obgyn|Gynaecology|Pelvic organ prolapse|Pelvic organ prolapse;Cystocele;Rectocele;Vault prolapse
obgyn|Gynaecology|Infections in gynecology/genital tract infection|Pelvic inflammatory disease;Tubo ovarian abscess;Vulvovaginal candidiasis;Bacterial vaginosis;Trichomoniasis;Chlamydial cervicitis;Gonococcal cervicitis
obgyn|Gynaecology|Fibroid|Uterine fibroid
obgyn|Gynaecology|Vulval & vaginal benign and premalignant conditions|Vulvar lichen sclerosus;Vulvar intraepithelial neoplasia;Bartholin abscess
obgyn|Gynaecology|Precancerous cervical lesion|Cervical intraepithelial neoplasia
obgyn|Gynaecology|Benign ovarian lesion|Mature cystic teratoma;Ovarian serous cystadenoma;Ovarian mucinous cystadenoma;Ovarian endometrioma;Ovarian torsion
obgyn|Gynaecology|Endometrial hyperplasia|Endometrial hyperplasia
obgyn|Gynaecology|Ovarian malignancy|Epithelial ovarian cancer;Dysgerminoma;Ovarian yolk sac tumor;Granulosa cell tumor;Sertoli Leydig cell tumor
obgyn|Gynaecology|Uterine malignancy|Endometrial carcinoma;Uterine leiomyosarcoma
obgyn|Gynaecology|Cervical malignancy|Cervical carcinoma
obgyn|Gynaecology|Vulval & vaginal malignancy|Vulvar squamous cell carcinoma;Vaginal carcinoma
obgyn|Gynaecology|Infertility|Tubal factor infertility;Anovulatory infertility;Male factor infertility;Ovarian hyperstimulation syndrome;Recurrent pregnancy loss;Antiphospholipid syndrome
pediatrics|Hematology|Anemias — IDA, G6PD, Thalassemia, Spherocytosis, Sickle Cell|Iron deficiency anemia;G6PD deficiency;Beta thalassemia major;Hereditary spherocytosis;Sickle cell disease;Acute chest syndrome
pediatrics|Hematology|Bleeding Disorders — ITP, Hemophilia, VWD|Immune thrombocytopenia;Hemophilia A;Von Willebrand disease
pediatrics|Hematology|Leukemias & Bone Marrow Failure — Aplastic Anemia|Acute lymphoblastic leukemia;Aplastic anemia
pediatrics|Neonatology|Neonatal care & APGAR|-
pediatrics|Neonatology|Neonatal jaundice|Physiological neonatal jaundice;Kernicterus;Biliary atresia
pediatrics|Neonatology|Prematurity & RDS|Neonatal respiratory distress syndrome;Transient tachypnea of the newborn;Necrotizing enterocolitis;Meconium aspiration syndrome
pediatrics|Neonatology|Neonatal sepsis|Neonatal sepsis
pediatrics|Neonatology|Birth injury|Erb palsy;Cephalohematoma;Subgaleal hemorrhage
pediatrics|Neonatology|Neonatal convulsion|Neonatal hypoglycemia;Neonatal hypocalcemia;Hypoxic ischemic encephalopathy
pediatrics|Neonatology|TORCH infections|Congenital cytomegalovirus infection;Congenital toxoplasmosis;Congenital rubella syndrome;Congenital syphilis
pediatrics|Gastrointestinal System|Infant feeding|Failure to thrive;Secondary lactose intolerance
pediatrics|Gastrointestinal System|Acute diarrhea — bloody/non-bloody|Acute gastroenteritis;Shigellosis
pediatrics|Gastrointestinal System|Dehydration & ORS|Dehydration
pediatrics|Gastrointestinal System|Persistent/chronic diarrhea — Celiac, post-infectious|Celiac disease;Secondary lactose intolerance
pediatrics|Gastrointestinal System|Malnutrition / FTT|Kwashiorkor;Marasmus;Failure to thrive
pediatrics|Gastrointestinal System|Acute hepatitis & fulminant hepatic failure|Hepatitis A;Acute liver failure
pediatrics|Gastrointestinal System|Chronic liver disease|Hepatic Wilson disease;Biliary atresia
pediatrics|Cardiovascular System|Cyanotic CHD — TOF, TGA|Tetralogy of Fallot;Transposition of the great arteries
pediatrics|Cardiovascular System|Acyanotic CHD — VSD, ASD, PDA|Ventricular septal defect;Atrial septal defect;Patent ductus arteriosus;Coarctation of the aorta
pediatrics|Cardiovascular System|Acquired heart disease — Rheumatic HD, Infective Endocarditis|Acute rheumatic fever;Infective endocarditis
pediatrics|Cardiovascular System|Heart failure|Congestive heart failure
pediatrics|Respiratory System|Asthma|Asthma
pediatrics|Respiratory System|Bronchiolitis|Bronchiolitis
pediatrics|Respiratory System|Pneumonia|Pneumonia
pediatrics|Respiratory System|URTI — Croup, Epiglottitis|Croup;Epiglottitis
pediatrics|Respiratory System|Recurrent RTI — CF, Bronchiectasis|Cystic fibrosis;Bronchiectasis
pediatrics|Infectious Diseases|Tuberculosis|Tuberculosis
pediatrics|Infectious Diseases|Exanthema — Scarlet fever, Measles, Mumps, Rubella, etc.|Scarlet fever;Measles;Mumps;Rubella;Roseola infantum;Erythema infectiosum;Hand foot and mouth disease
pediatrics|Infectious Diseases|Diphtheria|Diphtheria
pediatrics|Infectious Diseases|Pertussis|Pertussis
pediatrics|Infectious Diseases|Tetanus|Tetanus
pediatrics|Infectious Diseases|Kala azar|Visceral leishmaniasis
pediatrics|Infectious Diseases|Varicella|Varicella
pediatrics|Infectious Diseases|Infectious mononucleosis|Infectious mononucleosis
pediatrics|Infectious Diseases|PUO|-
pediatrics|Nephrology|UTI|Urinary tract infection
pediatrics|Nephrology|Acute renal failure|Prerenal acute kidney injury;Acute tubular injury
pediatrics|Nephrology|Nephrotic syndrome|Minimal change disease
pediatrics|Nephrology|Glomerulonephritis & Hypertension|Poststreptococcal glomerulonephritis;IgA nephropathy
pediatrics|Nephrology|Hematuria & HUS|Hemolytic uremic syndrome;IgA nephropathy
pediatrics|Central Nervous System|CNS infections — Meningitis, Encephalitis|Bacterial meningitis;Encephalitis
pediatrics|Central Nervous System|Acute paralysis|Guillain Barre syndrome;Acute flaccid myelitis
pediatrics|Central Nervous System|Epilepsy/Seizures & mimics|Simple febrile seizure;Absence epilepsy;Status epilepticus;Breath holding spells
pediatrics|Central Nervous System|Cerebral palsy|Spastic cerebral palsy
pediatrics|Endocrine|Rickets & Parathyroid disorders|Nutritional rickets;Hypoparathyroidism
pediatrics|Endocrine|Diabetes Mellitus|Type 1 diabetes mellitus;Diabetic ketoacidosis
pediatrics|Endocrine|Thyroid disorders — Hypo-/Hyperthyroidism|Congenital hypothyroidism;Acquired hypothyroidism;Graves disease
pediatrics|Endocrine|Short stature|Growth hormone deficiency;Familial short stature;Constitutional delay of growth and puberty
pediatrics|Genetics|Down & Turner syndromes|Down syndrome;Turner syndrome
pediatrics|Genetics|Types of inheritance|-
pediatrics|Rheumatology|Vasculitis — HSP, Kawasaki|IgA vasculitis;Kawasaki disease
pediatrics|Rheumatology|Connective tissue disease — JRA, SLE|Juvenile idiopathic arthritis;Systemic lupus erythematosus
pediatrics|Immunization|Vaccination schedule|-
pediatrics|Immunization|Side effects of vaccines|Vaccine associated anaphylaxis;BCG lymphadenitis
pediatrics|Growth & Development|Growth & Development Milestones|Global developmental delay;Failure to thrive
pediatrics|Others|Pediatric emergencies — CPA, Anaphylaxis, Status Epilepticus|Cardiac arrest;Anaphylaxis;Status epilepticus
pediatrics|Others|Poisoning|Iron poisoning;Salicylate poisoning;Paracetamol poisoning;Organophosphate poisoning
pediatrics|Others|Child abuse|Abusive head trauma
pediatrics|Others|Autism|Autism spectrum disorder
pediatrics|Others|Immunodeficiency|Severe combined immunodeficiency;X linked agammaglobulinemia;Chronic granulomatous disease
'''
# These rows have clinical examples, but encompass examinations, treatment, mechanisms,
# or wider diagnoses that are not fully represented by the listed examples.
PARTIAL_HINTS=('approach','classification','primary survey','secondary survey','imaging','instruments','anatomy','care','therapy','principles','management','repair','endoscopy','monitoring','induction','labour','labor','infant feeding','ORS','Milestones','1–12','prevention','transplantation','dialysis','Bariatric','Infertility','Contraception','Neonatal care','Chronic liver disease','Viral hepatitis, acute fulminant hepatic failure','Malnutrition, Obesity','Bleeding disorders','Bone/joint tumors','Metabolic bone diseases','Neurogenic bladder','Cleft lip','Hypogonadism, Hirsutism','Genetic & metabolic')

def audit():
    cases=json.loads((ROOT/'data/cases.json').read_text())
    index={}
    for case in cases:
        index.setdefault((case['specialty'],normalize(case['diagnosis'])),[]).append(case)
    rows=[]
    for line in ROWS.strip().splitlines():
        spec,section,topic,selections=line.split('|')
        examples=[]
        if selections!='-':
            for name in selections.split(';'):
                matches=index.get((spec,normalize(name)),[])
                if not matches:
                    raise ValueError(f'Crosswalk references missing case: {spec} / {name}')
                examples.extend(matches)
        if not examples:
            status='Not a standalone diagnosis / needs a separate curriculum mode'
        elif any(word.lower() in topic.lower() for word in PARTIAL_HINTS):
            status='Clinical examples only; wider curriculum partly represented'
        else:
            status='Clinical examples mapped; not an exhaustive disease list'
        rows.append({'specialty':spec,'section':section,'website_topic':topic,'status':status,
            'case_ids':list(dict.fromkeys(c['id'] for c in examples)),
            'diagnoses':list(dict.fromkeys(c['diagnosis'] for c in examples))})
    for c in cases:
        c['blueprint_topics']=[r['website_topic'] for r in rows if c['id'] in r['case_ids']]
    (ROOT/'data/cases.json').write_text(json.dumps(cases,indent=2,ensure_ascii=False)+'\n')
    (ROOT/'data/blueprint_topic_crosswalk.json').write_text(json.dumps({'source':'https://wizari.netlify.app/','inspected':'2026-10-02','note':'Nested website children are retained in grouped topic rows. Mappings are representative, not curricular completion scores.','rows':rows},indent=2,ensure_ascii=False)+'\n')
    old=json.loads((ROOT/'data/baseline_counts.json').read_text())
    lines=['# Blueprint audit and expansion — v2','','The website checklist was reinspected, including the topics inside all four specialties. Nested children are grouped with their displayed parent. A mapping means relevant clinical cases exist, not that every possible disease or the whole curriculum is covered.','',
      'The original 400 cases were retained. New clinical cases were appended with stable original IDs.','',
      '| Specialty | Before | Now | Added |','|---|---:|---:|---:|']
    for spec,label in SPECIALTIES.items():
        count=sum(c['specialty']==spec for c in cases)
        lines.append(f'| {label} | {old[spec]} | {count} | {count-old[spec]} |')
    lines+=['','## Surgery by branch','','| Branch | Before | Now | Added |','|---|---:|---:|---:|']
    before=json.loads((ROOT/'data/baseline_sections.json').read_text())
    sections=json.loads((ROOT/'data/blueprint_sections.json').read_text())['sections']['surgery']
    for section in sections:
        count=sum(c['specialty']=='surgery' and c['section']==section for c in cases)
        previous=before.get('surgery',{}).get(section,0)
        if section=='Radiology':
            lines.append('| Radiology | Imaging embedded | Imaging embedded | — |')
        else:
            lines.append(f'| {section} | {previous} | {count} | {count-previous} |')
    lines+=['','## Topic-to-case crosswalk','','Items involving procedures, physiology, screening schedules, ethics, or investigations still need a separate question format. Imaging appears inside the diagnostic cases. The rows below intentionally mark partial curricular representation instead of claiming full coverage.','']
    for spec,label in SPECIALTIES.items():
        lines+=[f'## {label}','','| Branch | Website topic | Clinical examples in the bank | Scope |','|---|---|---|---|']
        for row in rows:
            if row['specialty']!=spec: continue
            examples='; '.join(row['diagnoses']) or '—'
            scope='Examples only / broader topic' if 'partly' in row['status'] else 'Diagnosis cases' if row['case_ids'] else 'Separate curriculum mode needed'
            lines.append(f'| {row["section"]} | {row["website_topic"]} | {examples} | {scope} |')
        lines.append('')
    lines+=['## Remaining boundaries','','- Several site headings are open-ended (for example all cranial nerve palsies, all bowel disease, and all possible endocrine tumors). No finite diagnosis bank can be certified complete from those headings alone.',
      '- FUO/PUO is an approach to unexplained fever rather than a unique underlying disease; it is not a standalone answer in this version.',
      '- Diagnosis guessing does not replace management, prevention, anatomy, procedural or vaccination-schedule study.',
      '- These are newly authored educational cases, not official ministerial questions, and the complete bank has not undergone independent clinician review.','']
    (ROOT/'BLUEPRINT_AUDIT.md').write_text('\n'.join(lines),encoding='utf-8')
    print(f'Crosswalk: {len(rows)} grouped topic rows; {len({(r["specialty"],r["section"]) for r in rows})} branches audited.')

if __name__=='__main__': audit()
