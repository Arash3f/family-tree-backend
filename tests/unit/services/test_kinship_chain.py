"""The public kinship tool must name relations exactly as the app does."""

import pytest

from app.domain.services.kinship_chain import (
    MAX_KINSHIP_STEPS,
    KinshipStep,
    label_kinship_chain,
)

ZWNJ = "‌"
F, M = KinshipStep.FATHER, KinshipStep.MOTHER
SO, D = KinshipStep.SON, KinshipStep.DAUGHTER
B, SI = KinshipStep.BROTHER, KinshipStep.SISTER
H, W = KinshipStep.HUSBAND, KinshipStep.WIFE

# The same table the kinship page shows under the tool.
COMMON_RELATIONS = [
    ((F, F), "پدربزرگ", "grandfather"),
    ((F, M), "مادربزرگ", "grandmother"),
    ((F, B), "عمو", "paternal uncle"),
    ((F, SI), "عمه", "paternal aunt"),
    ((M, B), "دایی", "maternal uncle"),
    ((M, SI), "خاله", "maternal aunt"),
    ((F, B, SO), "پسرعمو", "paternal uncle's son"),
    ((F, B, D), "دخترعمو", "paternal uncle's daughter"),
    ((F, SI, SO), "پسرعمه", "paternal aunt's son"),
    ((F, SI, D), "دخترعمه", "paternal aunt's daughter"),
    ((M, B, SO), "پسردایی", "maternal uncle's son"),
    ((M, B, D), "دختردایی", "maternal uncle's daughter"),
    ((M, SI, SO), "پسرخاله", "maternal aunt's son"),
    ((M, SI, D), "دخترخاله", "maternal aunt's daughter"),
    ((B, SO), "برادرزاده", "nephew"),
    ((SI, D), "خواهرزاده", "niece"),
    ((SO, SO), "نوه", "grandson"),
    ((D, D), "نوه", "granddaughter"),
    ((SO, W), "عروس", "daughter-in-law"),
    ((D, H), "داماد", "son-in-law"),
    ((B, W), f"زن{ZWNJ}برادر", "sister-in-law"),
    ((SI, H), "شوهرخواهر", "brother-in-law"),
    ((F, B, W), f"زن{ZWNJ}عمو", "paternal uncle's wife"),
    ((F, SI, H), "شوهرعمه", "paternal aunt's husband"),
    ((M, B, W), f"زن{ZWNJ}دایی", "maternal uncle's wife"),
    ((M, SI, H), "شوهرخاله", "maternal aunt's husband"),
    ((W, F), "پدرزن", "father-in-law"),
    ((W, M), "مادرزن", "mother-in-law"),
    ((W, B), "برادرزن", "brother-in-law"),
    ((W, SI), "خواهرزن", "sister-in-law"),
    ((H, F), "پدرشوهر", "father-in-law"),
    ((H, M), "مادرشوهر", "mother-in-law"),
    ((H, B), "برادرشوهر", "brother-in-law"),
    ((H, SI), f"خواهر{ZWNJ}شوهر", "sister-in-law"),
    ((W, SI, H), "باجناق", "wife's sister's husband"),
    ((H, B, W), "جاری", "husband's brother's wife"),
    ((F, F, B), "برادرِ پدربزرگ", "grandfather's brother"),
]


@pytest.mark.parametrize(("steps", "label_fa", "label_en"), COMMON_RELATIONS)
def test_common_relations_are_named_like_the_app(steps, label_fa, label_en):
    labels = label_kinship_chain(steps)

    assert labels.label_fa == label_fa
    assert labels.label_en == label_en


def test_in_law_names_follow_the_speakers_gender():
    # "My wife's father" is said by a man, "my husband's father" by a woman.
    assert label_kinship_chain([W, F]).label_fa == "پدرزن"
    assert label_kinship_chain([H, F]).label_fa == "پدرشوهر"


def test_a_sibling_is_a_parent_and_a_child_in_the_description():
    labels = label_kinship_chain([B])

    assert labels.label_fa == "برادر"
    assert labels.description_en == "parent's son"


@pytest.mark.parametrize("length", [0, MAX_KINSHIP_STEPS + 1])
def test_chain_length_is_bounded(length):
    with pytest.raises(ValueError):
        label_kinship_chain([F] * length)
