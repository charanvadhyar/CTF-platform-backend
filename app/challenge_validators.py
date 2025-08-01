"""
Challenge validation logic for each CTF challenge.
Each validator function takes submission data and returns a SubmissionResult.
Simplified to only check the flag directly.
"""

from typing import Dict, Any
from app.models.challenge import SubmissionResult

# Dictionary of challenge flags
CHALLENGE_FLAGS = {
    1: "CTF{insecure_auth_logic_bypass}",
    2: "CTF{sql_injection_union_attack}",
    3: "CTF{reflected_xss_cookie_theft}",
    4: "CTF{cookie_manipulation_admin}",
    5: "CTF{security_through_obscurity_fails}",
    6: "CTF{never_trust_client_side_validation}",
    7: "CTF{idor_broken_access_control_vulnerability}",
    8: "CTF{open_redirect_no_validation}",
    9: "CTF{leaky_headers_reveal_secrets}",
    10: "CTF{jwt_none_alg_vulnerability}",
    11: "CTF{bypass_upload_filters_for_rce}",
    12: "CTF{r0b0ts_txt_d1scl0sur3_vuln}",
    13: "CTF{pr3d1ct4bl3_t0k3ns_4r3_1ns3cur3}",
    14: "CTF{csp_bypass_v1a_unsafe_eval}",
    15: "CTF{h4rdc0d3d_s3cr3ts_4r3_n3v3r_s4f3}"
}

def validate_flag(challenge_number: int, submission_data: Dict[str, Any]) -> SubmissionResult:
    """Universal flag validator that checks the submitted flag against the correct one"""
    # Extract flag from submission data
    submitted_flag = submission_data.get("flag", "")
    
    # Get expected flag for this challenge
    expected_flag = CHALLENGE_FLAGS.get(challenge_number)
    
    if not expected_flag:
        return SubmissionResult(
            success=False,
            message="Challenge not found",
            points_earned=0
        )
    
    # Compare flags (case-sensitive)
    if submitted_flag == expected_flag:
        return SubmissionResult(
            success=True,
            message="Flag is correct! Challenge solved.",
            flag=expected_flag,
            points_earned=10
        )
    
    return SubmissionResult(
        success=False,
        message="Incorrect flag. Keep trying!",
        points_earned=0
    )

# Define validation functions for challenge numbers 1-15
def validate_challenge_1(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(1, submission_data)

def validate_challenge_2(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(2, submission_data)

def validate_challenge_3(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(3, submission_data)

def validate_challenge_4(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(4, submission_data)

def validate_challenge_5(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(5, submission_data)

def validate_challenge_6(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(6, submission_data)

def validate_challenge_7(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(7, submission_data)

def validate_challenge_8(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(8, submission_data)

def validate_challenge_9(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(9, submission_data)

def validate_challenge_10(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(10, submission_data)

def validate_challenge_11(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(11, submission_data)

def validate_challenge_12(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(12, submission_data)

def validate_challenge_13(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(13, submission_data)

def validate_challenge_14(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(14, submission_data)

def validate_challenge_15(submission_data: Dict[str, Any]) -> SubmissionResult:
    return validate_flag(15, submission_data)

# Dictionary of challenge validators
CHALLENGE_VALIDATORS = {
    1: validate_challenge_1,
    2: validate_challenge_2,
    3: validate_challenge_3,
    4: validate_challenge_4,
    5: validate_challenge_5,
    6: validate_challenge_6,
    7: validate_challenge_7,
    8: validate_challenge_8,
    9: validate_challenge_9,
    10: validate_challenge_10,
    11: validate_challenge_11,
    12: validate_challenge_12,
    13: validate_challenge_13,
    14: validate_challenge_14,
    15: validate_challenge_15
}
