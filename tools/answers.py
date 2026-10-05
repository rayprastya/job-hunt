"""Shared screening-question answers, reused from easy_apply.py's rules (single source of truth).

from answers import get_answer; get_answer(question, kind, options, country)
"""
import os, re, sys, json

_src = open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "easy_apply.py")).read().split("# --- open the job")[0]
_src = re.sub(r"(?m)^TAB, JOB, COUNTRY = .*$", "COUNTRY = 'ID'", _src)
_src = re.sub(r"(?m)^a = AX\(TAB\)$", "a = None", _src)
_src = re.sub(r"(?m)^CV = ME\.require_cv\(\)$", "CV = None", _src)
_src = re.sub(r"(?m)^from ax import .*$", "", _src)
_ns = {"__file__": __file__}
exec(compile(_src, "easy_apply_rules", "exec"), _ns)


def _range_pick(n, options):
    """Map a number of years onto range-style options like '1-2 years', '3+ years', 'Less than 1 year'."""
    best = None
    for o in options:
        ol = o.lower()
        nums = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", ol)]
        if not nums:
            if n == 0 and re.search(r"none|no experience|less than", ol):
                return o
            continue
        if re.search(r"less than|under|<", ol) and n < nums[0]:
            return o
        if re.search(r"\+|more than|over|above|>", ol) and n >= nums[0]:
            best = o
        elif len(nums) >= 2 and nums[0] <= n <= nums[1]:
            return o
        elif len(nums) == 1 and n == nums[0]:
            return o
    return best


def get_answer(q, kind="text", options=None, country="ID"):
    _ns["COUNTRY"] = country
    ans = _ns["answer"](q, kind, options)
    if ans is not None and options and ans not in options and re.fullmatch(r"\d+", str(ans)):
        return _range_pick(int(ans), options)
    return ans
