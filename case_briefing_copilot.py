"""
case_briefing_copilot.py
========================
Generative Case Briefing Engine (Week 4)
----------------------------------------
Transforms raw FIR narratives and extracted legal/tactical entities into
an actionable, structured investigative intelligence dossier for Investigating
Officers (IO), Station House Officers (SHO), and Superintendents of Police (SP).

Statutory Framework:
  - Bharatiya Nyaya Sanhita (BNS) 2023
  - Bharatiya Sakshya Adhiniyam (BSA) 2023 [replaces Indian Evidence Act 1872]
  - Bharatiya Nagarik Suraksha Sanhita (BNSS) 2023 [replaces CrPC 1973]
  - Arms Act 1959 & NDPS Act 1985

Core Deliverables:
  a) Chronological Timeline of Events:
     - Multi-phase event reconstruction linking timestamps, actions, actors, and locations.
  b) Missing Evidence Gaps:
     - Identification of critical evidentiary deficiencies (weapon recovery under BSA §23,
       CCTV geo-telemetry, CDR/tower dump, MLC medico-legal certification, Panch witness).
  c) Suggested Suspect Interrogation Questions:
     - Psychologically and legally targeted interrogation inquiries with tactical objectives,
       anticipated evasion strategies, and evidentiary counter-probes.
"""

import re
import datetime
from typing import Dict, List, Any, Optional, Union


# ---------------------------------------------------------------------------
# Internal Entity & Signal Extractor (Self-Contained Fallback)
# ---------------------------------------------------------------------------

def _extract_entities_internal(text: str) -> Dict[str, Any]:
    """
    Self-contained extraction helper ensuring zero hard dependency on external modules.
    Extracts weapons, vehicles, phone numbers, locations, timestamps, and statutory markers.
    """
    clean_text = text.strip()
    lower_text = clean_text.lower()

    # 1. Weapons
    weapon_catalog = {
        'Firearms': [r'\bpistol\b', r'\brevolver\b', r'\bgun\b', r'\bkatta\b', r'\bdeshi katta\b', r'\brifle\b', r'\bcartridge[s]?\b', r'\bbullet[s]?\b'],
        'Edged Weapons': [r'\bknife\b', r'\bknives\b', r'\bmachete\b', r'\bmacchu\b', r'\btalwar\b', r'\bsword\b', r'\bblade\b', r'\bdagger\b'],
        'Blunt Weapons': [r'\biron rod\b', r'\blathi\b', r'\bstick\b', r'\bcrowbar\b', r'\bbrass knuckles\b', r'\bbaseball bat\b'],
        'Explosives / Hazardous': [r'\bbomb\b', r'\bied\b', r'\bgrenade\b', r'\bacid\b', r'\bpoison\b', r'\bpetrol bomb\b']
    }
    extracted_weapons = []
    for cat, pats in weapon_catalog.items():
        found = []
        for p in pats:
            matches = re.findall(p, lower_text)
            if matches:
                found.extend(matches)
        if found:
            extracted_weapons.append({'category': cat, 'items': sorted(list(set(found)))})

    # 2. Vehicles
    vehicle_regs = list(dict.fromkeys(re.findall(r'\b[A-Z]{2}[-\s]?\d{1,2}[-\s]?[A-Z]{1,3}[-\s]?\d{4}\b', clean_text)))
    vehicle_types = list(dict.fromkeys(re.findall(r'\b(?:motorcycle|bike|scooter|pulsar|swift|car|auto|autorickshaw|bolero|innova|scorpio|truck)\b', lower_text)))

    # 3. Phone numbers & digital markers
    phones = list(dict.fromkeys(re.findall(r'\b(?:\+?91[\-\s]?)?[6-9]\d{9}\b', clean_text)))

    # 4. Suspect names / aliases
    aliases = list(dict.fromkeys(re.findall(r'\b(?:alias|a\.k\.a\.?|known as)\s+[\'"]?([A-Za-z0-9_\-]+)[\'"]?', clean_text, re.IGNORECASE)))
    suspect_names = list(dict.fromkeys(re.findall(r'\b(?:accused|suspect|arrested)\s+(?:named|is)?\s*([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', clean_text)))

    # 5. Locations
    locations = list(dict.fromkeys(re.findall(
        r'\b[A-Z][a-zA-Z0-9\s\.\'-]{2,20}\s+(?:Nagar|Layout|Road|Street|Circle|Cross|Main|Marg|Colony|Junction|Flyover|Station|Bypass|Market)\b',
        clean_text
    )))
    city_matches = [
        c for c in ['Bengaluru', 'Bangalore', 'Mumbai', 'Delhi', 'Pune', 'Hyderabad', 'Chennai', 'Kolkata', 'Ahmedabad', 'Mysuru']
        if re.search(r'\b' + re.escape(c) + r'\b', clean_text, re.IGNORECASE)
    ]
    all_locations = list(dict.fromkeys(locations + city_matches))

    # 6. Dates and Timestamps
    time_matches = list(dict.fromkeys(re.findall(r'\b\d{1,2}:\d{2}(?::\d{2})?\s*(?:AM|PM|am|pm|hrs|hours)?\b', clean_text)))
    date_matches = list(dict.fromkeys(re.findall(r'\b(?:\d{1,2}[/-]\d{1,2}[/-]\d{2,4}|\d{4}[/-]\d{1,2}[/-]\d{1,2})\b', clean_text)))

    # 7. Financial & Stolen Property
    stolen_items = []
    cash_matches = re.findall(r'(?:Rs\.?|INR|amounting to|cash\s*(?:of)?)\s*([0-9,]+|\d+\s*(?:lakh|thousand)?)', clean_text, re.IGNORECASE)
    if cash_matches:
        stolen_items.append(f"Currency/Cash: {', '.join(cash_matches[:2])}")
    if re.search(r'\b(?:gold|chain|ornament|jewel|necklace|bangle)\b', lower_text):
        stolen_items.append("Gold / Jewelry items")
    if re.search(r'\b(?:mobile|phone|laptop|electronics|watch)\b', lower_text):
        stolen_items.append("Electronic Gadgets / Watches")

    return {
        'weapons': extracted_weapons,
        'vehicles': {'registrations': vehicle_regs, 'models': vehicle_types},
        'phones': phones,
        'suspects': {'aliases': aliases, 'names': suspect_names},
        'locations': all_locations,
        'times': time_matches,
        'dates': date_matches,
        'stolen_property': stolen_items
    }


# ---------------------------------------------------------------------------
# 1. Chronological Timeline Reconstruction Engine
# ---------------------------------------------------------------------------

def _build_chronological_timeline(narrative: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Reconstruct a multi-phase chronological timeline of the criminal incident.
    Identifies pre-incident approach, confrontation execution, escape/evasion,
    and post-incident police/medical reporting.
    """
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', narrative) if len(s.strip()) > 10]
    dates = entities.get('dates', [])
    times = entities.get('times', [])
    locations = entities.get('locations', [])

    date_str = dates[0] if dates else datetime.date.today().strftime("%d/%m/%Y")
    timeline: List[Dict[str, Any]] = []
    step_num = 1

    # Stage A: Ingress / Approach
    approach_sents = [s for s in sentences if re.search(r'\b(?:approach|intercept|riding|driving|waiting|spotted|arrived|vehicle|motorcycle)\b', s, re.I)]
    primary_time = times[0] if times else "Approx. 22:30 HRS"
    primary_loc = locations[0] if locations else "Incident Vicinity"

    if approach_sents:
        timeline.append({
            'step_number': step_num,
            'phase': 'Pre-Incident / Ingress',
            'time_marker': f"{date_str} at {primary_time}",
            'location': primary_loc,
            'event_description': approach_sents[0],
            'tactical_significance': 'Approach trajectory, vehicle identification, and ingress corridor.',
            'actors': 'Suspects on vehicle / Surveillance telemetry'
        })
        step_num += 1

    # Stage B: Direct Confrontation / Commission of Offense
    confront_sents = [s for s in sentences if re.search(r'\b(?:fired|brandished|knife|pistol|threatened|hurt|assault|snatched|stole|robbed|extorted|injured|demanded|broken|shutters)\b', s, re.I)]
    if confront_sents:
        confront_desc = " ".join(confront_sents[:2])
        timeline.append({
            'step_number': step_num,
            'phase': 'Offense Execution / Direct Assault',
            'time_marker': f"{primary_time} + 5 mins",
            'location': primary_loc,
            'event_description': confront_desc,
            'tactical_significance': 'Active physical offense, lethal weapon deployment, and extortion of property.',
            'actors': 'Armed Suspects vs Victim'
        })
        step_num += 1

    # Stage C: Evasion / Flight from Scene
    escape_sents = [s for s in sentences if re.search(r'\b(?:fled|escaped|fleeing|sped|ran|departed|direction|towards|highway|road)\b', s, re.I)]
    secondary_loc = locations[1] if len(locations) > 1 else f"Egress route from {primary_loc}"
    if escape_sents:
        timeline.append({
            'step_number': step_num,
            'phase': 'Egress / Escape Trajectory',
            'time_marker': f"{primary_time} + 12 mins",
            'location': secondary_loc,
            'event_description': escape_sents[0],
            'tactical_significance': 'Flight path, ANPR camera interception window, and evasion mode.',
            'actors': 'Suspects fleeing'
        })
        step_num += 1

    # Stage D: Post-Incident First Response & Reporting
    response_sents = [s for s in sentences if re.search(r'\b(?:reported|patrol|hospital|fir|discovered|admitted|police station|complainant)\b', s, re.I)]
    resp_time = times[1] if len(times) > 1 else (f"{primary_time} + 30 mins" if times else "Early Morning Hours")
    resp_desc = response_sents[0] if response_sents else f"Complainant lodged formal report at local jurisdictional police station following incident at {primary_loc}."
    timeline.append({
        'step_number': step_num,
        'phase': 'Police First Response & FIR Registration',
        'time_marker': resp_time,
        'location': primary_loc,
        'event_description': resp_desc,
        'tactical_significance': 'Initial formal statement, medical triage, and evidence preservation window.',
        'actors': 'Complainant / Patrol Unit / Investigating Officer'
    })

    # Fallback if text was very short
    if len(timeline) < 2:
        timeline.insert(0, {
            'step_number': 1,
            'phase': 'Occurrence of Crime',
            'time_marker': primary_time,
            'location': primary_loc,
            'event_description': narrative[:250] + '...',
            'tactical_significance': 'Core factual occurrence detailed in complainant narrative.',
            'actors': 'Perpetrator & Victim'
        })
        for idx, item in enumerate(timeline, 1):
            item['step_number'] = idx

    return timeline


# ---------------------------------------------------------------------------
# 2. Missing Evidence Gaps Engine
# ---------------------------------------------------------------------------

def _detect_missing_evidence_gaps(narrative: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Identify missing evidentiary, forensic, and statutory gaps under
    Bharatiya Nyaya Sanhita 2023 and Bharatiya Sakshya Adhiniyam 2023.
    """
    gaps: List[Dict[str, Any]] = []
    clean_lower = narrative.lower()
    weapons = entities.get('weapons', [])
    vehicles = entities.get('vehicles', {})
    phones = entities.get('phones', [])
    locations = entities.get('locations', [])

    gap_counter = 1

    # 1. Weapon Seizure & Ballistic Analysis Gap
    if weapons:
        weapon_names = ", ".join([w.get('category', 'weapon') for w in weapons])
        has_seizure_memo = bool(re.search(r'\b(?:recovered|seized|panchnama|in custody|confiscated|recovery memo)\b', clean_lower))
        if not has_seizure_memo:
            gaps.append({
                'gap_id': f"GAP-0{gap_counter}",
                'category': 'Physical Weapon & Forensic Ballistics',
                'priority': 'CRITICAL',
                'statutory_reference': 'Bharatiya Sakshya Adhiniyam (BSA) 2023 §23 (Information leading to discovery)',
                'deficiency_summary': f"Weapons ({weapon_names}) identified in narrative remain unrecovered from suspects.",
                'recommended_action': 'Execute custodial disclosure statement under BSA §23; retrieve physical weapons; dispatch to State Forensic Science Laboratory (FSL) for ballistic striation and fingerprint matching.'
            })
            gap_counter += 1

    # 2. CCTV & Geo-Trajectory Telemetry Gap
    has_cctv_seized = bool(re.search(r'\b(?:cctv\s*(?:seized|collected|retrieved|secured)|footage\s*(?:obtained|examined))\b', clean_lower))
    if not has_cctv_seized:
        loc_str = locations[0] if locations else "scene of occurrence and escape routes"
        gaps.append({
            'gap_id': f"GAP-0{gap_counter}",
            'category': 'Digital Video Telemetry (CCTV)',
            'priority': 'HIGH',
            'statutory_reference': 'BSA 2023 §63 (Electronic Records Admissibility) & BNSS §105',
            'deficiency_summary': f"No formal seizure of CCTV DVR recordings along ingress and flight trajectories near {loc_str}.",
            'recommended_action': f"Subpoena and secure CCTV telemetry from private establishments, traffic cameras, and fuel stations within 1 km of {loc_str}; certify via BSA §63 certificate."
        })
        gap_counter += 1

    # 3. CDR / IPDR & Cell Tower Dump Analysis Gap
    has_cdr_requested = bool(re.search(r'\b(?:cdr\s*(?:analyzed|obtained)|tower\s*dump|call\s*records)\b', clean_lower))
    if phones or not has_cdr_requested:
        target_phones = ", ".join(phones) if phones else "suspect handsets active in cell tower radius"
        gaps.append({
            'gap_id': f"GAP-0{gap_counter}",
            'category': 'Telecommunications & Cell-Site Intelligence',
            'priority': 'HIGH',
            'statutory_reference': 'Indian Telegraph Act §5(2) & BNSS §94 (Summons to produce document/telemetry)',
            'deficiency_summary': f"Call Detail Records (CDR) and cell-tower dump for {target_phones} not logged in case diary.",
            'recommended_action': "Submit Section 94 BNSS requisition to Telecom Service Providers (TSPs) for CDR, IPDR, IMEI history, and B-party subscriber identity verification."
        })
        gap_counter += 1

    # 4. Vehicle ANPR & Ownership Verification Gap
    vehicle_regs = vehicles.get('registrations', [])
    vehicle_models = vehicles.get('models', [])
    if vehicle_regs or vehicle_models:
        v_target = vehicle_regs[0] if vehicle_regs else vehicle_models[0]
        gaps.append({
            'gap_id': f"GAP-0{gap_counter}",
            'category': 'Automated Number-Plate Recognition (ANPR)',
            'priority': 'HIGH',
            'statutory_reference': 'Motor Vehicles Act §213 & BNSS §173',
            'deficiency_summary': f"Escape vehicle ({v_target}) ownership and route trajectory have not been verified via RTO VAHAN database or ANPR feeds.",
            'recommended_action': f"Query Smart City Command & Control Center (ICCC) ANPR logs for vehicle {v_target}; cross-reference chassis number against state stolen vehicle database."
        })
        gap_counter += 1

    # 5. Medico-Legal Examination & Biological Evidence (MLC)
    has_injury = bool(re.search(r'\b(?:bleeding|hurt|injured|assault|grievous|stabbed|shot|hospital)\b', clean_lower))
    has_mlc = bool(re.search(r'\b(?:mlc|medico[- ]legal|doctor|fsl swab|post[- ]mortem)\b', clean_lower))
    if has_injury and not has_mlc:
        gaps.append({
            'gap_id': f"GAP-0{gap_counter}",
            'category': 'Medico-Legal Certification & Biological Swabs',
            'priority': 'CRITICAL',
            'statutory_reference': 'BNSS 2023 §51 & §53 (Medical examination of victim and accused)',
            'deficiency_summary': 'Injury/wound described in narrative without an accompanying Medico-Legal Certificate (MLC) or wound certificate.',
            'recommended_action': 'Escort victim/injured parties to District Hospital for immediate MLC issuance; preserve clothing and obtain biological DNA blood-swabs for FSL match.'
        })
        gap_counter += 1

    # 6. Panch Witness & Test Identification Parade (TIP)
    gaps.append({
        'gap_id': f"GAP-0{gap_counter}",
        'category': 'Independent Corroboration & Test Identification Parade (TIP)',
        'priority': 'MEDIUM',
        'statutory_reference': 'BSA 2023 §7 & BNSS 2023 §54',
        'deficiency_summary': 'Independent panchas (witnesses) not yet cross-examined; Test Identification Parade (TIP) required for non-apprehended co-suspects.',
        'recommended_action': 'Record statements under Section 180 BNSS of independent shopkeepers and security guards; file application before Executive Magistrate for formal TIP.'
    })

    return gaps


# ---------------------------------------------------------------------------
# 3. Suggested Suspect Interrogation Questions Engine
# ---------------------------------------------------------------------------

def _generate_interrogation_questions(narrative: str, entities: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Construct psychologically and forensically tactical interrogation inquiries
    to deconstruct alibis, establish weapon custody, trace money trails, and expose accomplices.
    """
    questions: List[Dict[str, Any]] = []
    weapons = entities.get('weapons', [])
    vehicles = entities.get('vehicles', {})
    suspects = entities.get('suspects', {})
    locations = entities.get('locations', [])
    times = entities.get('times', [])
    dates = entities.get('dates', [])
    stolen = entities.get('stolen_property', [])

    primary_time = times[0] if times else "the time of the occurrence"
    primary_date = dates[0] if dates else "the date in question"
    primary_loc = locations[0] if locations else "the scene of crime"

    q_num = 1

    # 1. Alibi Deconstruction Question
    questions.append({
        'question_id': f"INT-0{q_num}",
        'target_area': 'Alibi Deconstruction & Geolocation',
        'question_text': f"State your exact physical location, companions, and phone usage between {primary_time} and 3 hours thereafter on {primary_date}. Who can verify your physical presence?",
        'tactical_objective': 'Lock the suspect into a rigid, falsifiable timeline prior to confronting them with cell-tower and CCTV records.',
        'expected_evasive_response': "'I was asleep at home' or 'I was with friends in another neighborhood.'",
        'counter_probe': f"Cell-site telemetry places your active handset within 300 meters of {primary_loc} at that exact minute. How do you explain this convergence?"
    })
    q_num += 1

    # 2. Weapon Possession & Disclosure Question
    if weapons:
        w_name = weapons[0]['items'][0] if weapons[0].get('items') else "the weapon"
        questions.append({
            'question_id': f"INT-0{q_num}",
            'target_area': 'Weapon Procurement & Custody (BSA §23)',
            'question_text': f"Where is the {w_name} used during the incident at {primary_loc} currently hidden, and from which source did you procure it?",
            'tactical_objective': 'Elicit an admissible discovery disclosure statement under BSA 2023 Section 23 leading directly to physical weapon recovery.',
            'expected_evasive_response': "'I never carried any weapon; the complainant is falsely implicating me.'",
            'counter_probe': f"Witness statements and ballistic casing marks confirm a {w_name} was discharged. Failure to disclose location forfeits mitigating factors during remand hearing."
        })
        q_num += 1

    # 3. Vehicle Operator & Escape Route Question
    v_regs = vehicles.get('registrations', [])
    v_models = vehicles.get('models', [])
    if v_regs or v_models:
        v_ident = v_regs[0] if v_regs else v_models[0]
        questions.append({
            'question_id': f"INT-0{q_num}",
            'target_area': 'Vehicle Telemetry & Route Verification',
            'question_text': f"Who was operating the {v_ident} seen fleeing from {primary_loc}, and where was that vehicle parked after midnight?",
            'tactical_objective': 'Establish ownership, driver identity, and identify whether fake number plates were utilized.',
            'expected_evasive_response': "'I lent my vehicle to an acquaintance earlier that evening' or 'That was not my vehicle.'",
            'counter_probe': f"High-resolution ANPR cameras captured your facial contour at the toll/junction heading away from {primary_loc}. Who was seated on the pillion/passenger seat?"
        })
        q_num += 1

    # 4. Accomplice & Handler Question
    aliases = suspects.get('aliases', [])
    alias_str = f"known as '{aliases[0]}'" if aliases else "operating with you"
    questions.append({
        'question_id': f"INT-0{q_num}",
        'target_area': 'Co-Conspirators & Syndicated Linkages',
        'question_text': f"Identify the individual {alias_str} who accompanied you during the approach, and name the handler who planned this target.",
        'tactical_objective': 'Break conspiratorial silence under BNS §61 (Criminal Conspiracy) / BNS §111 (Organized Crime).',
        'expected_evasive_response': "'I was acting alone' or 'I do not know anyone by that alias.'",
        'counter_probe': "We have synchronized call records and UPI transaction ties linking you to this alias over the past 30 days. We are already raiding their residence."
    })
    q_num += 1

    # 5. Stolen Property & Proceeds of Crime
    if stolen:
        stolen_str = ", ".join(stolen)
        questions.append({
            'question_id': f"INT-0{q_num}",
            'target_area': 'Stolen Property Recovery & Financial Trail',
            'question_text': f"Where have you disposed of the {stolen_str} taken from the victim, and which receiver or jeweler did you pledge it to?",
            'tactical_objective': 'Facilitate property seizure under BNSS §106 and invoke BNS §317 (Receiving stolen property).',
            'expected_evasive_response': "'I didn't take any valuables; nothing was found in my pockets.'",
            'counter_probe': "Surveillance clearly shows the package being removed. Disclosing the receiver immediately will allow recovery before the gold/property is melted."
        })
        q_num += 1

    # 6. Motive & Digital Communications
    questions.append({
        'question_id': f"INT-0{q_num}",
        'target_area': 'Motive & Prior Surveillance Reconnaissance',
        'question_text': f"How many times did you conduct reconnaissance on {primary_loc} prior to the incident, and who provided internal layout intelligence?",
        'tactical_objective': 'Prove premeditation and Mens Rea, disqualifying claims of sudden altercation or accidental presence.',
        'expected_evasive_response': "'I happened to be passing by by chance.'",
        'counter_probe': "Nearby CCTV footage reveals your vehicle making two slow passes past the complainant's location 48 hours prior. Why was that necessary?"
    })

    return questions


# ---------------------------------------------------------------------------
# 4. Public API: Generate Case Brief
# ---------------------------------------------------------------------------

def generate_case_brief(case_narrative: str, entities_dict: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Generate a comprehensive, structured case briefing dossier from FIR narrative
    and legal/tactical entities.

    Parameters
    ----------
    case_narrative : str
        The narrative text of the FIR, case report, or witness statement.
    entities_dict : dict, optional
        Pre-extracted entities from case_parser or NER pipeline. If None,
        the internal extraction pipeline automatically processes the narrative.

    Returns
    -------
    dict
        Structured JSON-serializable case briefing containing:
          a) Chronological Timeline of Events (`chronological_timeline`)
          b) Missing Evidence Gaps (`missing_evidence_gaps`)
          c) Suggested Suspect Interrogation Questions (`suggested_interrogation_questions`)
          d) Executive Case Synopsis (`executive_summary`)
    """
    if not case_narrative or not case_narrative.strip():
        return {
            'status': 'error',
            'message': 'case_narrative cannot be empty.'
        }

    clean_text = case_narrative.strip()

    # Step 1: Resolve entities (use passed dictionary or extract automatically)
    if entities_dict and isinstance(entities_dict, dict) and any(entities_dict.values()):
        # Normalize external entity structure
        entities = {
            'weapons': entities_dict.get('weapons', []),
            'vehicles': entities_dict.get('tactical_signals', {}).get('vehicles', entities_dict.get('vehicles', {})),
            'phones': entities_dict.get('tactical_signals', {}).get('phone_numbers', entities_dict.get('phones', [])),
            'suspects': entities_dict.get('suspects', {'aliases': entities_dict.get('tactical_signals', {}).get('suspect_aliases', [])}),
            'locations': entities_dict.get('locations', entities_dict.get('incident_location', [])),
            'times': entities_dict.get('timeline', []),
            'dates': entities_dict.get('dates', []),
            'stolen_property': entities_dict.get('stolen_property', [])
        }
    else:
        entities = _extract_entities_internal(clean_text)

    # Step 2: Build Deliverables
    timeline = _build_chronological_timeline(clean_text, entities)
    evidence_gaps = _detect_missing_evidence_gaps(clean_text, entities)
    interrogation_qs = _generate_interrogation_questions(clean_text, entities)

    # Step 3: Executive Summary Metadata
    critical_gaps_count = sum(1 for g in evidence_gaps if g['priority'] == 'CRITICAL')
    severity_rating = "CRITICAL INVESTIGATION" if critical_gaps_count >= 2 else ("HIGH PRIORITY" if critical_gaps_count == 1 else "STANDARD OPERATIONAL")

    return {
        'status': 'success',
        'generated_at': datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        'statutory_framework': 'Bharatiya Nyaya Sanhita 2023 (BNS) & Bharatiya Sakshya Adhiniyam 2023 (BSA)',
        'executive_summary': {
            'investigation_priority': severity_rating,
            'total_timeline_phases': len(timeline),
            'total_evidence_gaps': len(evidence_gaps),
            'critical_gaps_count': critical_gaps_count,
            'total_interrogation_questions': len(interrogation_qs),
            'key_locations': entities.get('locations', [])[:3],
            'primary_weapons': [w.get('category') for w in entities.get('weapons', [])] if entities.get('weapons') else ['None reported']
        },
        'chronological_timeline': timeline,
        'missing_evidence_gaps': evidence_gaps,
        'suggested_interrogation_questions': interrogation_qs
    }
