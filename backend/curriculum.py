"""Senior Phase mathematics: topic detection, lessons, practice, and working."""

from __future__ import annotations

import ast
import math
import re
from fractions import Fraction

CONTENT = {
    "whole_numbers": "Numbers, operations and relationships",
    "exponents": "Numbers, operations and relationships",
    "integers": "Numbers, operations and relationships",
    "fractions": "Numbers, operations and relationships",
    "decimals": "Numbers, operations and relationships",
    "finance": "Numbers, operations and relationships",
    "patterns": "Patterns, functions and algebra",
    "functions": "Patterns, functions and algebra",
    "expressions": "Patterns, functions and algebra",
    "equations": "Patterns, functions and algebra",
    "graphs": "Patterns, functions and algebra",
    "straight_lines": "Space and shape (geometry)",
    "geometry_2d": "Space and shape (geometry)",
    "pythagoras": "Measurement",
    "area": "Measurement",
    "volume": "Measurement",
    "data": "Data handling",
    "probability": "Data handling",
}

NAMES = {
    "whole_numbers": "Whole numbers",
    "exponents": "Exponents",
    "integers": "Integers",
    "fractions": "Common fractions",
    "decimals": "Decimal fractions",
    "finance": "Financial mathematics",
    "patterns": "Numeric and geometric patterns",
    "functions": "Functions and relationships",
    "expressions": "Algebraic expressions",
    "equations": "Algebraic equations",
    "graphs": "Graphs",
    "straight_lines": "Geometry of straight lines",
    "geometry_2d": "Geometry of 2D shapes",
    "pythagoras": "Theorem of Pythagoras",
    "area": "Area and perimeter",
    "volume": "Surface area and volume",
    "data": "Data handling",
    "probability": "Probability",
}

# Term placement used for syllabus, papers, and progress.
PLACEMENT = {
    7: {
        1: ["whole_numbers", "exponents"],
        2: ["fractions", "decimals", "integers"],
        3: ["patterns", "functions", "expressions", "equations"],
        4: ["straight_lines", "geometry_2d", "area", "data", "probability"],
    },
    8: {
        1: ["whole_numbers", "integers", "exponents"],
        2: ["fractions", "decimals", "patterns", "expressions"],
        3: ["equations", "straight_lines", "geometry_2d", "pythagoras"],
        4: ["graphs", "area", "volume", "data"],
    },
    9: {
        1: ["whole_numbers", "integers", "exponents", "patterns"],
        2: ["expressions", "equations", "functions"],
        3: ["straight_lines", "geometry_2d", "graphs", "finance"],
        4: ["pythagoras", "area", "volume", "data", "probability"],
    },
}

NOTES = {
    "whole_numbers": {
        7: "Calculation techniques, multiples and factors, ratio and rate.",
        8: "Revision of calculations, HCF, LCM, ratio and rate in context.",
        9: "Properties of numbers, factorisation of whole numbers, and problem solving.",
    },
    "exponents": {
        7: "Squares to 12², cubes to 6³, and calculations with small exponents.",
        8: "Comparing exponential form, including scientific notation of large numbers.",
        9: "Laws of exponents, including negative exponents and very small numbers.",
    },
    "integers": {
        7: "Ordering, number lines, and addition and subtraction of integers.",
        8: "All four operations, multiple operations, and additive inverses.",
        9: "Revision of multiple operations, and additive and multiplicative inverses.",
    },
    "fractions": {
        7: "Equivalent fractions, mixed numbers, and addition with unrelated denominators.",
        8: "All four operations with fractions, and percentage increase or decrease.",
        9: "Fraction calculations used inside algebraic and measurement problems.",
    },
    "decimals": {
        7: "Place value, ordering, and addition and subtraction of decimal fractions.",
        8: "Multiplication and division of decimals, and links to percentages.",
        9: "Decimal calculations kept correct to a sensible number of places.",
    },
    "finance": {
        7: "Percentage of an amount, used with fraction work.",
        8: "Percentage increase and decrease in everyday contexts.",
        9: "Profit and loss, VAT, simple interest, and compound interest.",
    },
    "patterns": {
        7: "Extend a pattern and describe the rule in words.",
        8: "Describe the rule in words or with algebra.",
        9: "Find a general rule and use it to find a later term.",
    },
    "functions": {
        7: "Input and output values from a verbal rule, flow diagram, or table.",
        8: "Input and output values from a formula or an equation.",
        9: "Equivalent forms of the same relationship.",
    },
    "expressions": {
        7: "Recognise variables, constants, and like terms.",
        8: "Expand and simplify algebraic expressions.",
        9: "Expand, simplify, and factorise, including a difference of squares.",
    },
    "equations": {
        7: "Number sentences solved by inspection.",
        8: "Linear equations in one variable, checked by substitution.",
        9: "Equations with fractions, and products of factors equal to zero.",
    },
    "graphs": {
        7: "Read a value from a table or a set of axes.",
        8: "Interpret and draw straight-line graphs.",
        9: "Gradient, intercept, and the link between a rule and its graph.",
    },
    "straight_lines": {
        7: "Adjacent angles on a straight line, and vertically opposite angles.",
        8: "Parallel lines cut by a transversal.",
        9: "Reasons for each statement: corresponding, alternate, and co-interior angles.",
    },
    "geometry_2d": {
        7: "Triangles and quadrilaterals classified by sides and angles.",
        8: "Properties of triangles and quadrilaterals, including angle sums.",
        9: "Congruence, similarity, and the exterior angle of a triangle.",
    },
    "pythagoras": {
        7: "Square numbers that later support the theorem.",
        8: "The relationship between the sides of a right-angled triangle.",
        9: "Missing lengths in context, including diagonals of rectangles.",
    },
    "area": {
        7: "Perimeter and area of rectangles and triangles.",
        8: "Perimeter and area of polygons and circles, using π = 22/7 where asked.",
        9: "The effect on area when a dimension is multiplied by a factor.",
    },
    "volume": {
        7: "Volume and surface area of cubes and rectangular prisms.",
        8: "Rectangular prisms, triangular prisms, and cylinders.",
        9: "The effect on volume when one or more dimensions are multiplied by k.",
    },
    "data": {
        7: "Mode and range of a small data set.",
        8: "Mean, median, mode, and range of ungrouped data.",
        9: "Compare two sets, and notice how an outlier affects the mean.",
    },
    "probability": {
        7: "Equally likely outcomes, such as a coin or a die.",
        8: "Probability as a fraction of equally likely outcomes.",
        9: "Probability from a described collection of outcomes.",
    },
}

PHRASES: dict[str, list[tuple[str, int]]] = {
    "whole_numbers": [
        ("highest common factor", 8), ("lowest common multiple", 8), ("hcf", 7), ("lcm", 7),
        ("prime factor", 6), ("whole number", 5), ("rounding", 4), ("ratio", 4), ("rate", 4),
        ("long division", 5), ("multiples", 3), ("sharing in a given ratio", 6),
    ],
    "exponents": [
        ("laws of exponents", 8), ("law of exponents", 8), ("scientific notation", 7),
        ("square root", 6), ("cube root", 6), ("to the power", 6), ("exponent", 6),
        ("index law", 6), ("squared", 4), ("cubed", 4), ("power of", 4),
    ],
    "integers": [
        ("additive inverse", 8), ("multiplicative inverse", 7), ("negative number", 6),
        ("number line", 5), ("integer", 6), ("directed number", 5),
    ],
    "fractions": [
        ("common fraction", 7), ("mixed number", 6), ("improper fraction", 6),
        ("equivalent fraction", 6), ("numerator", 4), ("denominator", 4),
        ("simplest form", 4), ("percentage of", 5), ("% of", 5),
    ],
    "decimals": [
        ("decimal fraction", 7), ("decimal", 5), ("tenths", 4), ("hundredths", 4),
        ("recurring", 4),
    ],
    "finance": [
        ("simple interest", 9), ("compound interest", 9), ("hire purchase", 7),
        ("exchange rate", 6), ("percentage profit", 7), ("profit and loss", 6),
        ("vat", 5), ("interest", 4),
    ],
    "patterns": [
        ("geometric pattern", 7), ("numeric pattern", 7), ("number pattern", 6),
        ("common difference", 6), ("next term", 5), ("sequence", 4), ("general rule", 5),
    ],
    "functions": [
        ("flow diagram", 7), ("input and output", 7), ("input value", 5),
        ("output value", 5), ("function", 4),
    ],
    "expressions": [
        ("like terms", 7), ("algebraic expression", 7), ("factorise", 6), ("factorize", 6),
        ("expand and simplify", 7), ("difference of squares", 7), ("coefficient", 4),
        ("expression", 3),
    ],
    "equations": [
        ("solve for", 6), ("algebraic equation", 7), ("linear equation", 7),
        ("number sentence", 5), ("equation", 4),
    ],
    "graphs": [
        ("y-intercept", 7), ("gradient", 6), ("cartesian", 5), ("straight-line graph", 7),
        ("plot the graph", 5), ("intercept", 3),
    ],
    "straight_lines": [
        ("vertically opposite", 8), ("co-interior", 8), ("corresponding angle", 7),
        ("alternate angle", 7), ("transversal", 6), ("straight line", 5),
        ("adjacent angle", 5), ("supplementary", 4),
    ],
    "geometry_2d": [
        ("equilateral", 6), ("isosceles", 6), ("parallelogram", 5), ("quadrilateral", 5),
        ("exterior angle", 6), ("congruent", 5), ("similar triangle", 6),
        ("compass", 3), ("protractor", 4), ("angle sum", 5),
    ],
    "pythagoras": [
        ("pythagoras", 9), ("hypotenuse", 8), ("right-angled triangle", 7),
        ("right angled triangle", 7),
    ],
    "area": [
        ("perimeter", 6), ("area of", 6), ("circumference", 6), ("square units", 3),
    ],
    "volume": [
        ("surface area", 8), ("volume", 6), ("capacity", 4), ("cylinder", 4),
        ("rectangular prism", 6), ("cubic", 3),
    ],
    "data": [
        ("median", 6), ("mode", 5), ("mean", 4), ("range of", 4), ("data set", 5),
        ("stem-and-leaf", 6), ("outlier", 5), ("tally", 3),
    ],
    "probability": [
        ("probability", 8), ("equally likely", 6), ("outcome", 3), ("relative frequency", 6),
    ],
}


def topic_id(grade: int, concept: str) -> str:
    return f"g{grade}-{concept}"


def term_of(grade: int, concept: str) -> int | None:
    for term, concepts in PLACEMENT.get(grade, {}).items():
        if concept in concepts:
            return term
    return None


def first_home(concept: str) -> tuple[int, int] | None:
    for grade in (7, 8, 9):
        term = term_of(grade, concept)
        if term:
            return grade, term
    return None


def syllabus(grade: int) -> list[dict]:
    terms = []
    for term in (1, 2, 3, 4):
        topics = []
        for concept in PLACEMENT[grade][term]:
            topics.append(describe(grade, concept))
        terms.append({"term": term, "topics": topics})
    return terms


def describe(grade: int, concept: str) -> dict:
    return {
        "id": topic_id(grade, concept),
        "concept": concept,
        "name": NAMES[concept],
        "grade": grade,
        "term": term_of(grade, concept),
        "content_area": CONTENT[concept],
        "note": NOTES[concept][grade],
    }


def concepts_for_grade(grade: int) -> list[str]:
    found = []
    for term in (1, 2, 3, 4):
        found.extend(PLACEMENT[grade][term])
    return found


def classify(question: str, grade: int, forced: str | None = None) -> dict:
    if forced and forced in NAMES:
        concept = forced
    else:
        concept = best_concept(question, grade)
    home_term = term_of(grade, concept)
    in_grade = home_term is not None
    if not in_grade:
        home = first_home(concept)
        taught_grade, taught_term = home if home else (grade, 1)
    else:
        taught_grade, taught_term = grade, home_term
    score = phrase_score(question).get(concept, 0)
    if score >= 8:
        confidence = "high"
    elif score >= 4:
        confidence = "fair"
    else:
        confidence = "low"
    if in_grade:
        reason = f"The wording matches {NAMES[concept]} in the Grade {grade} Term {taught_term} syllabus."
    else:
        reason = (
            f"The wording matches {NAMES[concept]}. "
            f"In this curriculum that topic is set in Grade {taught_grade}, Term {taught_term}."
        )
    alternatives = []
    ranked = sorted(phrase_score(question).items(), key=lambda item: item[1], reverse=True)
    for other, other_score in ranked:
        if other == concept or other_score < 4:
            continue
        if other in concepts_for_grade(grade):
            alternatives.append({
                "concept": other,
                "name": NAMES[other],
                "term": term_of(grade, other),
                "id": topic_id(grade, other),
            })
        if len(alternatives) == 2:
            break
    return {
        "concept": concept,
        "topic": describe(grade if in_grade else taught_grade, concept) | {
            "id": topic_id(grade, concept) if in_grade else topic_id(taught_grade, concept),
        },
        "in_grade": in_grade,
        "confidence": confidence,
        "reason": reason,
        "alternatives": alternatives,
        "keywords": [phrase for phrase, _weight in PHRASES[concept][:6]],
    }


def phrase_score(question: str) -> dict[str, int]:
    text = f" {question.lower()} "
    text = text.replace("−", "-").replace("×", "x")
    scores = {concept: 0 for concept in NAMES}
    for concept, phrases in PHRASES.items():
        for phrase, weight in phrases:
            if phrase in text:
                scores[concept] += weight
    if re.search(r"\d\s*\^\s*\d", text) or re.search(r"\d\s*(st|nd|rd|th)?\s*power", text):
        scores["exponents"] += 6
    if re.search(r"(^|[^a-z])-\s*\d", text) or "(-" in text:
        scores["integers"] += 4
    if re.search(r"\d\s*/\s*\d", text) and "equation" not in text and "solve" not in text:
        scores["fractions"] += 4
    if re.search(r"\d+[.,]\d+", text) and "interest" not in text:
        scores["decimals"] += 3
    if re.search(r"\d+\s*x|solve", text):
        scores["equations"] += 3
    if "%" in text and "interest" not in text and "profit" not in text and "vat" not in text:
        scores["fractions"] += 4
    return scores


def best_concept(question: str, grade: int) -> str:
    scores = phrase_score(question)
    solved = solve_question(question)
    if solved:
        scores[solved["concept"]] = scores.get(solved["concept"], 0) + 10
    in_grade = {concept: score for concept, score in scores.items() if term_of(grade, concept)}
    best_any = max(scores, key=scores.get)
    best_here = max(in_grade, key=in_grade.get) if in_grade else best_any
    if scores[best_any] >= in_grade.get(best_here, 0) + 6 and scores[best_any] >= 6:
        return best_any
    if in_grade.get(best_here, 0) > 0:
        return best_here
    return best_any if scores[best_any] > 0 else PLACEMENT[grade][1][0]


def keywords_for(concept: str) -> list[str]:
    return [phrase for phrase, _weight in PHRASES[concept]]


def lesson(grade: int, concept: str) -> dict:
    example = EXAMPLE(concept)(grade)
    practice = PRACTICE(concept)(grade)
    return {
        "steps": STEPS[concept],
        "mistakes": MISTAKES[concept],
        "example": example,
        "practice": practice,
    }


def _num(value) -> str:
    if isinstance(value, float):
        if abs(value - round(value)) < 1e-9:
            return str(int(round(value)))
        return f"{value:.2f}".rstrip("0").rstrip(".")
    return str(value)


def _money(value) -> str:
    if abs(value - round(value)) < 1e-9:
        return f"R{int(round(value))}"
    return f"R{value:.2f}"


STEPS = {
    "whole_numbers": [
        "Decide whether the problem is a calculation, a factor question, a ratio, or a rate.",
        "For a product, break the multiplier into tens and units and add the partial products.",
        "For HCF, list the prime factors and keep only the ones shared by both numbers.",
        "For a ratio, add the parts first, then find the value of one part.",
    ],
    "exponents": [
        "Read the base and the exponent. The exponent says how many times the base is a factor.",
        "When multiplying powers with the same base, add the exponents.",
        "When dividing powers with the same base, subtract the exponents.",
        "A power of a power: multiply the exponents. A non-zero number to the power 0 is 1.",
    ],
    "integers": [
        "Use a number line. Positive moves right and negative moves left.",
        "Subtracting a negative is the same as adding its opposite.",
        "A negative times a negative is positive. A negative times a positive is negative.",
        "Do multiplication and division before addition and subtraction.",
    ],
    "fractions": [
        "Write mixed numbers as improper fractions before calculating.",
        "To add or subtract, rewrite both fractions with a common denominator.",
        "To multiply, multiply the numerators and multiply the denominators, then simplify.",
        "A percentage is a fraction out of 100. 15% of an amount is 15/100 of that amount.",
    ],
    "decimals": [
        "Line up the decimal points before adding or subtracting.",
        "When multiplying, count the decimal digits in the question. The answer needs the same count.",
        "Check the size of the answer by estimating with whole numbers.",
    ],
    "finance": [
        "Simple interest uses SI = P × n × r / 100. P is the principal, n the years, r the rate.",
        "For compound interest, add each year's interest to the principal before the next year.",
        "Percentage profit is profit divided by cost price, multiplied by 100.",
        "VAT at 15% is 15/100 of the price before VAT.",
    ],
    "patterns": [
        "Write the difference between consecutive terms. If it stays the same, the pattern is linear.",
        "The general term of a linear pattern has the form an + b.",
        "Check the rule on the first term before using it for a later term.",
    ],
    "functions": [
        "The input is the number you start with. Apply the rule once, in the order given.",
        "A formula such as y = 3x + 1 means multiply the input by 3, then add 1.",
        "A table, a flow diagram, and a formula can describe the same relationship.",
    ],
    "expressions": [
        "Like terms have the same variables and the same powers. Only like terms combine.",
        "To expand a bracket, multiply every term inside by the factor outside.",
        "Collect like terms only after every bracket has been expanded.",
        "A difference of squares factors as a² − b² = (a − b)(a + b).",
    ],
    "equations": [
        "Keep the equation balanced. What you do to one side, do to the other.",
        "Use the additive inverse to move a constant, and the multiplicative inverse to clear a coefficient.",
        "If a product of factors is zero, at least one of the factors is zero.",
        "Substitute the answer back into the original equation to check it.",
    ],
    "graphs": [
        "In y = mx + c, m is the gradient and c is the y-intercept.",
        "The gradient is the change in y for each one-unit increase in x.",
        "Substitute an x-value into the rule to find the matching y-value.",
    ],
    "straight_lines": [
        "Adjacent angles on a straight line add to 180°.",
        "Vertically opposite angles are equal.",
        "When a transversal cuts parallel lines, corresponding angles are equal and co-interior angles add to 180°.",
    ],
    "geometry_2d": [
        "The interior angles of a triangle add to 180°. The interior angles of a quadrilateral add to 360°.",
        "An exterior angle of a triangle equals the sum of the two interior opposite angles.",
        "Classify a triangle by its sides and again by its angles.",
    ],
    "pythagoras": [
        "The theorem applies only to a right-angled triangle.",
        "The hypotenuse is the side opposite the right angle, and it is the longest side.",
        "If the two shorter sides are a and b, then a² + b² = c².",
        "To find a shorter side, subtract the known square from the hypotenuse squared.",
    ],
    "area": [
        "Area of a rectangle is length × breadth. Perimeter is the distance around the boundary.",
        "Area of a triangle is ½ × base × height. The height is perpendicular to the base.",
        "Circumference of a circle is 2πr. Area of a circle is πr².",
    ],
    "volume": [
        "Volume of a rectangular prism is length × breadth × height.",
        "Surface area is the total area of the faces. A cube has six identical square faces.",
        "Volume of a cylinder is πr²h. State the value of π you were asked to use.",
    ],
    "data": [
        "Order the values before finding the median. The median is the middle value.",
        "The mode is the value that appears most often. A set can have more than one mode.",
        "The mean is the sum of the values divided by how many values there are.",
        "The range is the highest value minus the lowest value.",
    ],
    "probability": [
        "If outcomes are equally likely, probability is the number of favourable outcomes over the total.",
        "Write the probability as a simplified fraction.",
        "A probability of 0 means impossible, and a probability of 1 means certain.",
    ],
}

MISTAKES = {
    "whole_numbers": [
        "Adding the partial products incorrectly after a column multiplication.",
        "Confusing HCF with LCM. The HCF is never larger than the smaller number.",
    ],
    "exponents": [
        "Multiplying the bases as well as the exponents when the bases are the same.",
        "Reading 2³ as 2 × 3 instead of 2 × 2 × 2.",
    ],
    "integers": [
        "Working from left to right and ignoring that multiplication comes before addition.",
        "Treating two negatives next to each other as a single negative.",
    ],
    "fractions": [
        "Adding the denominators as well as the numerators.",
        "Forgetting to convert a mixed number before multiplying.",
    ],
    "decimals": [
        "Lining up the right-hand digits instead of the decimal points.",
        "Dropping a zero that is holding a decimal place.",
    ],
    "finance": [
        "Using the selling price, instead of the cost price, as the base for percentage profit.",
        "Forgetting to divide by 100 in the simple-interest formula.",
    ],
    "patterns": [
        "Using the position number as if it were already the term.",
        "Checking the rule on the second term and skipping the first.",
    ],
    "functions": [
        "Adding before multiplying when the rule says multiply, then add.",
        "Swapping the input and the output.",
    ],
    "expressions": [
        "Combining unlike terms, such as an x-term and a constant.",
        "Multiplying only the first term inside a bracket.",
    ],
    "equations": [
        "Changing the sign of a term without doing the same operation to both sides.",
        "Forgetting the solution x = 0 when a product of factors equals zero.",
    ],
    "graphs": [
        "Swapping the gradient and the y-intercept in y = mx + c.",
        "Counting blocks on the axes when the scale is not 1 unit per block.",
    ],
    "straight_lines": [
        "Assuming every pair of angles on a diagram is equal.",
        "Using 90° for a straight line instead of 180°.",
    ],
    "geometry_2d": [
        "Using 180° as the angle sum of a quadrilateral.",
        "Calling a triangle equilateral when only two sides are equal.",
    ],
    "pythagoras": [
        "Adding the sides instead of adding the squares.",
        "Treating a shorter side as the hypotenuse.",
    ],
    "area": [
        "Using the slanted side as the height of a triangle.",
        "Reporting a perimeter when the question asks for area.",
    ],
    "volume": [
        "Giving surface area in cubic units, or volume in square units.",
        "Using the diameter in the cylinder formula where the radius is required.",
    ],
    "data": [
        "Choosing the middle value before ordering the data.",
        "Dividing by the largest value instead of by the number of values when finding the mean.",
    ],
    "probability": [
        "Writing the probability as a whole number of outcomes instead of a fraction.",
        "Forgetting to simplify the fraction.",
    ],
}


def EXAMPLE(concept):
    return {
        "whole_numbers": example_whole,
        "exponents": example_exponents,
        "integers": example_integers,
        "fractions": example_fractions,
        "decimals": example_decimals,
        "finance": example_finance,
        "patterns": example_patterns,
        "functions": example_functions,
        "expressions": example_expressions,
        "equations": example_equations,
        "graphs": example_graphs,
        "straight_lines": example_lines,
        "geometry_2d": example_shapes,
        "pythagoras": example_pythagoras,
        "area": example_area,
        "volume": example_volume,
        "data": example_data,
        "probability": example_probability,
    }[concept]


def PRACTICE(concept):
    return {
        "whole_numbers": practice_whole,
        "exponents": practice_exponents,
        "integers": practice_integers,
        "fractions": practice_fractions,
        "decimals": practice_decimals,
        "finance": practice_finance,
        "patterns": practice_patterns,
        "functions": practice_functions,
        "expressions": practice_expressions,
        "equations": practice_equations,
        "graphs": practice_graphs,
        "straight_lines": practice_lines,
        "geometry_2d": practice_shapes,
        "pythagoras": practice_pythagoras,
        "area": practice_area,
        "volume": practice_volume,
        "data": practice_data,
        "probability": practice_probability,
    }[concept]


def _worked(prompt, steps, answer, accept=None):
    return {
        "prompt": prompt,
        "steps": steps,
        "answer": _num(answer) if not isinstance(answer, str) else answer,
        "accept": accept or ([_num(answer)] if not isinstance(answer, str) else [answer]),
    }


def example_whole(grade: int):
    pairs = {7: (346, 28), 8: (208, 36), 9: (125, 48)}
    a, b = pairs[grade]
    tens, units = (b // 10) * 10, b % 10
    return _worked(
        f"Calculate {a} × {b}.",
        [
            f"Break {b} into {tens} + {units}.",
            f"{a} × {tens} = {a * tens}.",
            f"{a} × {units} = {a * units}.",
            "Add the partial products.",
        ],
        a * b,
    )


def practice_whole(grade: int):
    if grade == 7:
        left, right = 36, 48
        ratio_total, r1, r2 = 250, 2, 3
    elif grade == 8:
        left, right = 84, 126
        ratio_total, r1, r2 = 360, 4, 5
    else:
        left, right = 180, 252
        ratio_total, r1, r2 = 480, 5, 3
    hcf = math.gcd(left, right)
    lcm = abs(left * right) // hcf
    part = ratio_total // (r1 + r2)
    return [
        _worked(
            f"Find the HCF of {left} and {right}.",
            [
                "Write each number as a product of primes, or use successive division.",
                "Multiply only the prime factors that appear in both numbers.",
            ],
            hcf,
        ),
        _worked(
            f"Find the LCM of {left} and {right}.",
            [
                f"The HCF of {left} and {right} is {hcf}.",
                "LCM = product of the two numbers ÷ HCF.",
            ],
            lcm,
        ),
        _worked(
            f"Share R{ratio_total} in the ratio {r1} : {r2}. Give the larger share.",
            [
                f"There are {r1 + r2} equal parts.",
                f"One part is R{part}.",
                f"The shares are R{part * r1} and R{part * r2}.",
            ],
            part * max(r1, r2),
            accept=[str(part * max(r1, r2)), _money(part * max(r1, r2))],
        ),
    ]


def example_exponents(grade: int):
    if grade == 7:
        return _worked(
            "Calculate 2³ × 2⁴.",
            [
                "The bases are the same, so add the exponents.",
                "2³ × 2⁴ = 2⁷.",
                "2⁷ means seven factors of 2.",
            ],
            2 ** 7,
            accept=["128", "2^7", "2⁷"],
        )
    if grade == 8:
        return _worked(
            "Write 81 as a power of 3.",
            [
                "3 × 3 = 9, 9 × 3 = 27, and 27 × 3 = 81.",
                "81 is four factors of 3.",
            ],
            "3^4",
            accept=["3^4", "3⁴", "81"],
        )
    return _worked(
        "Simplify 5⁶ ÷ 5⁴. Give the value.",
        [
            "The bases are the same, so subtract the exponents.",
            "5⁶ ÷ 5⁴ = 5².",
        ],
        25,
        accept=["25", "5^2", "5²"],
    )


def practice_exponents(grade: int):
    if grade == 7:
        return [
            _worked("Calculate 12².", ["12² = 12 × 12."], 144, accept=["144", "12^2"]),
            _worked("Calculate 5³.", ["5³ = 5 × 5 × 5."], 125),
            _worked(
                "Simplify 3² × 3³ and give the value.",
                ["Add the exponents: 3⁵.", "3⁵ = 243."],
                243,
                accept=["243", "3^5"],
            ),
        ]
    if grade == 8:
        return [
            _worked("Calculate the square root of 196.", ["14 × 14 = 196."], 14),
            _worked("Calculate the cube root of −8.", ["(−2) × (−2) × (−2) = −8."], -2, accept=["-2"]),
            _worked(
                "Calculate 4⁵ ÷ 4³.",
                ["Subtract the exponents: 4².", "4² = 16."],
                16,
                accept=["16", "4^2"],
            ),
        ]
    return [
        _worked(
            "Simplify 2⁻³. Give the value as a fraction.",
            ["A negative exponent gives the reciprocal.", "2⁻³ = 1/2³ = 1/8."],
            "1/8",
            accept=["1/8", "0.125"],
        ),
        _worked(
            "Simplify (3²)³ and give the value.",
            ["Multiply the exponents: 3⁶.", "3⁶ = 729."],
            729,
            accept=["729", "3^6"],
        ),
        _worked("Any non-zero number to the power 0 equals what?", ["By the zero-exponent law, a⁰ = 1."], 1),
    ]


def example_integers(grade: int):
    if grade == 7:
        return _worked(
            "Calculate −6 + 9.",
            ["Start at −6.", "Adding 9 moves 9 units to the right."],
            3,
        )
    if grade == 8:
        return _worked(
            "Calculate −8 + 5 × −2.",
            [
                "Multiply before you add.",
                "5 × −2 = −10.",
                "Then −8 + (−10).",
            ],
            -18,
        )
    return _worked(
        "Calculate −15 − (−6).",
        ["Subtracting a negative is the same as adding the opposite.", "−15 + 6."],
        -9,
    )


def practice_integers(grade: int):
    if grade == 7:
        items = [(-4, 7, -4 + 7), (-9, -3, -12), (5, -8, -3)]
        return [
            _worked(f"Calculate {a} + {b}.", ["Move along the number line from the first integer."], result)
            for a, b, result in items
        ]
    if grade == 8:
        return [
            _worked("Calculate −12 + 7 − 4.", ["−12 + 7 = −5.", "Then −5 − 4."], -9),
            _worked("Calculate (−6) × (−4).", ["A negative times a negative is positive."], 24),
            _worked("What is the additive inverse of −15?", ["The additive inverse sums with the number to give 0."], 15),
        ]
    return [
        _worked("Calculate 18 ÷ (−3) + 4.", ["18 ÷ (−3) = −6.", "Then −6 + 4."], -2),
        _worked("Calculate (−2)³.", ["(−2) × (−2) × (−2) = −8."], -8),
        _worked(
            "What is the multiplicative inverse of −4? Give it as a fraction.",
            ["The product of a number and its multiplicative inverse is 1."],
            "-1/4",
            accept=["-1/4", "-0.25"],
        ),
    ]


def example_fractions(grade: int):
    if grade == 9:
        return _worked(
            "Calculate 3/4 of 36.",
            ["1/4 of 36 is 9.", "3/4 is three of those parts."],
            27,
        )
    total = Fraction(1, 2) + Fraction(1, 3)
    return _worked(
        "Calculate 1/2 + 1/3.",
        [
            "The lowest common denominator of 2 and 3 is 6.",
            "1/2 = 3/6 and 1/3 = 2/6.",
            "Add the numerators.",
        ],
        "5/6",
        accept=["5/6", "0.83", "0.833"],
    )


def practice_fractions(grade: int):
    if grade == 7:
        value = Fraction(2, 3) + Fraction(1, 4)
        return [
            _worked(
                "Calculate 2/3 + 1/4. Give the answer as a fraction.",
                ["The common denominator is 12.", "8/12 + 3/12."],
                "11/12",
                accept=["11/12"],
            ),
            _worked("Calculate 3/5 of 40.", ["1/5 of 40 is 8.", "3/5 is 24."], 24),
            _worked("Write 18/24 in simplest form.", ["Divide the numerator and the denominator by 6."], "3/4", accept=["3/4"]),
        ]
    if grade == 8:
        return [
            _worked("Calculate 15% of 240.", ["15% = 15/100.", "0.15 × 240."], 36),
            _worked(
                "Increase 200 by 10%.",
                ["10% of 200 is 20.", "Add the increase to 200."],
                220,
            ),
            _worked(
                "Calculate 2/3 × 3/4. Give the answer in simplest form.",
                ["Multiply numerators and denominators.", "6/12 simplifies by 6."],
                "1/2",
                accept=["1/2", "0.5"],
            ),
        ]
    return [
        _worked("Calculate 12.5% of 480.", ["12.5% = 1/8.", "480 ÷ 8."], 60),
        _worked(
            "Calculate 3/4 − 2/5. Give the answer as a fraction.",
            ["The common denominator is 20.", "15/20 − 8/20."],
            "7/20",
            accept=["7/20"],
        ),
        _worked("Calculate 2 1/2 × 4.", ["2 1/2 = 5/2.", "5/2 × 4 = 10."], 10, accept=["10", "5/2*4"]),
    ]


def example_decimals(grade: int):
    if grade >= 8:
        return _worked(
            "Calculate 2.5 × 0.4.",
            ["25 × 4 = 100.", "There are two decimal digits in the question, so the answer is 1.00."],
            "1",
            accept=["1", "1.0", "1.00"],
        )
    return _worked(
        "Calculate 3.75 + 2.6.",
        ["Line up the decimal points.", "2.6 is 2.60.", "Add hundredths, then tenths, then units."],
        "6.35",
        accept=["6.35"],
    )


def practice_decimals(grade: int):
    return [
        _worked("Calculate 8.4 − 2.75.", ["8.40 − 2.75."], "5.65", accept=["5.65"]),
        _worked("Calculate 0.6 × 0.6.", ["6 × 6 = 36, with two decimal digits."], "0.36", accept=["0.36"]),
        _worked("Round 45.682 to two decimal places.", ["The third decimal digit is 2, so the 8 stays."], "45.68", accept=["45.68"]),
    ]


def example_finance(grade: int):
    principal, rate, years = (600, 7, 3) if grade >= 9 else (2000, 8, 3)
    interest = principal * rate * years / 100
    return _worked(
        f"Calculate the simple interest on {_money(principal)} at {rate}% per year for {years} years.",
        [
            "Use SI = P × n × r / 100.",
            f"P = {principal}, n = {years}, r = {rate}.",
            f"{principal} × {years} × {rate} / 100.",
        ],
        interest,
        accept=[_num(interest), _money(interest)],
    )


def practice_finance(grade: int):
    principal, rate, years = (800, 6, 4) if grade < 9 else (3450, 6, 2)
    # keep grade 9 compound separate
    interest = principal * rate * years / 100
    items = [
        _worked(
            f"Calculate the simple interest on {_money(principal)} at {rate}% per year for {years} years.",
            [f"SI = {principal} × {years} × {rate} / 100."],
            interest,
            accept=[_num(interest), _money(interest)],
        )
    ]
    if grade >= 9:
        amount = 500 * (1.08 ** 2)
        items.append(_worked(
            "R500 is borrowed at 8% per year compound interest for 2 years. How much is owed at the end?",
            [
                "After year 1 the amount is 500 × 1.08 = 540.",
                "After year 2 the amount is 540 × 1.08.",
            ],
            round(amount, 2),
            accept=["583.20", "R583.20", "583.2"],
        ))
        items.append(_worked(
            "An item costs R250 and is sold for R310. What is the percentage profit?",
            ["Profit = 310 − 250 = 60.", "Percentage profit = 60/250 × 100."],
            24,
            accept=["24", "24%"],
        ))
    else:
        items.append(_worked(
            "Calculate 15% VAT on R400.",
            ["VAT = 15/100 × 400."],
            60,
            accept=["60", "R60"],
        ))
        items.append(_worked(
            "A price of R80 is reduced by 25%. What is the new price?",
            ["25% of 80 is 20.", "Subtract the discount."],
            60,
            accept=["60", "R60"],
        ))
    return items


def example_patterns(grade: int):
    if grade == 9:
        return _worked(
            "The pattern is 4, 7, 10, 13, …. Find the 20th term.",
            [
                "The common difference is 3, so the rule has the form 3n + b.",
                "The first term is 3(1) + 1 = 4, so the rule is 3n + 1.",
                "Substitute n = 20.",
            ],
            61,
        )
    return _worked(
        "The pattern is 5, 8, 11, 14, …. Write the next term.",
        ["The common difference is 3.", "Add 3 to the last given term."],
        17,
    )


def practice_patterns(grade: int):
    if grade == 7:
        return [
            _worked("Write the next term in 6, 10, 14, 18, ….", ["The common difference is 4."], 22),
            _worked("Write the next term in 2, 4, 8, 16, ….", ["Each term is doubled."], 32),
            _worked("The rule is 'multiply the position by 5'. What is the 4th term?", ["5 × 4."], 20),
        ]
    if grade == 8:
        return [
            _worked("The pattern is 3, 7, 11, 15, …. What is the common difference?", ["7 − 3 = 4, and the difference stays constant."], 4),
            _worked("Using the rule 2n + 1, find the 6th term.", ["2 × 6 + 1."], 13),
            _worked("Write the next term in 1, 4, 9, 16, ….", ["These are the square numbers. The next is 5²."], 25),
        ]
    return [
        _worked("The pattern is 5, 8, 11, 14, …. Find the 15th term.", ["The rule is 3n + 2.", "3 × 15 + 2."], 47),
        _worked("The pattern is 2, 6, 10, 14, …. Find the 10th term.", ["The rule is 4n − 2.", "4 × 10 − 2."], 38),
        _worked("A pattern has the rule 5n − 3. What is the first term?", ["Substitute n = 1."], 2),
    ]


def example_functions(grade: int):
    if grade == 7:
        return _worked(
            "The rule is: multiply the input by 3, then subtract 1. The input is 4. Find the output.",
            ["4 × 3 = 12.", "12 − 1."],
            11,
        )
    return _worked(
        "Use y = 4x − 1. Find y when x = 6.",
        ["Substitute 6 for x.", "4 × 6 − 1."],
        23,
    )


def practice_functions(grade: int):
    return [
        _worked("The rule is: add 5, then multiply by 2. The input is 3. Find the output.", ["3 + 5 = 8.", "8 × 2."], 16),
        _worked("Use y = 2x + 5. Find y when x = 7.", ["2 × 7 + 5."], 19),
        _worked("A flow diagram multiplies by 4. The output is 28. What was the input?", ["28 ÷ 4."], 7),
    ]


def example_expressions(grade: int):
    if grade == 7:
        return _worked(
            "Simplify 5x + 3x.",
            ["5x and 3x are like terms.", "Add the coefficients."],
            "8x",
            accept=["8x", "8*x"],
        )
    if grade == 8:
        return _worked(
            "Expand and simplify 4(x + 2) + 3x.",
            ["4(x + 2) = 4x + 8.", "4x + 3x + 8.", "7x + 8."],
            "7x+8",
            accept=["7x+8", "8+7x"],
        )
    return _worked(
        "Expand and simplify 3(x − 2) − 2(x + 4).",
        ["3(x − 2) = 3x − 6.", "−2(x + 4) = −2x − 8.", "3x − 2x − 6 − 8."],
        "x-14",
        accept=["x-14", "1x-14", "-14+x"],
    )


def practice_expressions(grade: int):
    if grade == 7:
        return [
            _worked("Simplify 7a + 2a − 4a.", ["Combine the like terms."], "5a", accept=["5a"]),
            _worked("In the expression 6x + 4, what is the coefficient of x?", ["The coefficient is the number multiplying the variable."], 6),
            _worked("Simplify 9y − y.", ["9y − 1y."], "8y", accept=["8y"]),
        ]
    if grade == 8:
        return [
            _worked("Expand and simplify 2(x + 5) + 4.", ["2x + 10 + 4."], "2x+14", accept=["2x+14", "14+2x"]),
            _worked("Simplify 8x + 3 − 3x + 2.", ["8x − 3x and 3 + 2."], "5x+5", accept=["5x+5", "5+5x"]),
            _worked("Expand 5(2x − 1).", ["Multiply both terms by 5."], "10x-5", accept=["10x-5", "-5+10x"]),
        ]
    return [
        _worked("Factorise x² − 9.", ["This is a difference of squares.", "(x − 3)(x + 3)."], "(x-3)(x+3)", accept=["(x-3)(x+3)", "(x+3)(x-3)"]),
        _worked("Expand and simplify 2(x − 4) + 3(x + 1).", ["2x − 8 + 3x + 3."], "5x-5", accept=["5x-5", "-5+5x"]),
        _worked("Simplify −3(2x − 5).", ["−3 × 2x and −3 × −5."], "-6x+15", accept=["-6x+15", "15-6x"]),
    ]


def example_equations(grade: int):
    if grade == 7:
        return _worked(
            "Solve the number sentence x + 9 = 15.",
            ["Ask which number, added to 9, gives 15.", "Subtract 9 from both sides."],
            6,
            accept=["6", "x=6"],
        )
    if grade == 8:
        return _worked(
            "Solve 3x − 4 = 11.",
            ["Add 4 to both sides: 3x = 15.", "Divide both sides by 3."],
            5,
            accept=["5", "x=5"],
        )
    return _worked(
        "Solve 2(x − 3) = 10.",
        ["Divide both sides by 2: x − 3 = 5.", "Add 3 to both sides."],
        8,
        accept=["8", "x=8"],
    )


def practice_equations(grade: int):
    if grade == 7:
        return [
            _worked("Solve x + 7 = 20.", ["Subtract 7 from both sides."], 13, accept=["13", "x=13"]),
            _worked("Solve 4x = 28.", ["Divide both sides by 4."], 7, accept=["7", "x=7"]),
            _worked("Solve x − 6 = 9.", ["Add 6 to both sides."], 15, accept=["15", "x=15"]),
        ]
    if grade == 8:
        return [
            _worked("Solve 2x + 5 = 19.", ["Subtract 5, then divide by 2."], 7, accept=["7", "x=7"]),
            _worked("Solve 5x − 3 = 22.", ["Add 3, then divide by 5."], 5, accept=["5", "x=5"]),
            _worked("Solve x/4 = 6.", ["Multiply both sides by 4."], 24, accept=["24", "x=24"]),
        ]
    return [
        _worked("Solve 3(x − 2) = 15.", ["Divide by 3, then add 2."], 7, accept=["7", "x=7"]),
        _worked(
            "Solve x² − 9x = 0. Give both solutions.",
            ["Factorise: x(x − 9) = 0.", "So x = 0 or x = 9."],
            "0 or 9",
            accept=["0 or 9", "0,9", "9 or 0", "x=0 or x=9", "0 and 9"],
        ),
        _worked("Solve (x − 4)/2 = 5.", ["Multiply both sides by 2, then add 4."], 14, accept=["14", "x=14"]),
    ]


def example_graphs(grade: int):
    return _worked(
        "For the graph of y = 2x + 1, what is the gradient?",
        ["The rule is written as y = mx + c.", "The number multiplying x is the gradient."],
        2,
    )


def practice_graphs(grade: int):
    return [
        _worked("For y = 3x − 4, what is the y-intercept?", ["In y = mx + c, c is the y-intercept."], -4, accept=["-4", "(0,-4)", "0,-4"]),
        _worked("For y = 2x + 1, find y when x = 3.", ["Substitute x = 3."], 7),
        _worked("A straight line rises 6 units for a run of 2 units. What is the gradient?", ["Gradient = rise ÷ run."], 3),
    ]


def example_lines(grade: int):
    if grade >= 8:
        return _worked(
            "Two parallel lines are cut by a transversal. One co-interior angle is 65°. Find the other.",
            ["Co-interior angles are supplementary.", "180° − 65°."],
            115,
            accept=["115", "115°"],
        )
    return _worked(
        "Two adjacent angles lie on a straight line. One is 73°. Find the other.",
        ["Angles on a straight line add to 180°.", "180° − 73°."],
        107,
        accept=["107", "107°"],
    )


def practice_lines(grade: int):
    if grade == 7:
        return [
            _worked("An angle on a straight line is 48°. Find the adjacent angle.", ["180 − 48."], 132, accept=["132", "132°"]),
            _worked("Two lines intersect. One angle is 35°. Find the vertically opposite angle.", ["Vertically opposite angles are equal."], 35, accept=["35", "35°"]),
            _worked("Two angles on a straight line are equal. How large is each?", ["180 ÷ 2."], 90, accept=["90", "90°"]),
        ]
    return [
        _worked("A corresponding angle to 118° is formed by a transversal and parallel lines. How large is it?", ["Corresponding angles are equal."], 118, accept=["118", "118°"]),
        _worked("A co-interior angle is 72°. Find the other co-interior angle.", ["180 − 72."], 108, accept=["108", "108°"]),
        _worked("An alternate angle to 46° is marked. How large is it?", ["Alternate angles are equal."], 46, accept=["46", "46°"]),
    ]


def example_shapes(grade: int):
    if grade == 9:
        return _worked(
            "An exterior angle of a triangle is 110°. One interior opposite angle is 40°. Find the other.",
            ["The exterior angle equals the sum of the two interior opposite angles.", "110 − 40."],
            70,
            accept=["70", "70°"],
        )
    if grade == 8:
        return _worked(
            "Three angles of a quadrilateral are 80°, 95° and 110°. Find the fourth.",
            ["The interior angles of a quadrilateral add to 360°.", "360 − 80 − 95 − 110."],
            75,
            accept=["75", "75°"],
        )
    return _worked(
        "A triangle has angles of 50° and 60°. Find the third angle.",
        ["The angles of a triangle add to 180°.", "180 − 50 − 60."],
        70,
        accept=["70", "70°"],
    )


def practice_shapes(grade: int):
    if grade == 7:
        return [
            _worked(
                "What do we call a triangle with all three sides equal?",
                ["Three equal sides is the definition used in this grade."],
                "equilateral",
                accept=["equilateral", "equilateral triangle"],
            ),
            _worked(
                "A triangle has angles 40° and 40°. What kind of triangle is it, by its sides?",
                ["Two equal angles mean two equal sides."],
                "isosceles",
                accept=["isosceles", "isosceles triangle"],
            ),
            _worked("Two angles of a triangle are 90° and 35°. Find the third.", ["180 − 90 − 35."], 55, accept=["55", "55°"]),
        ]
    if grade == 8:
        return [
            _worked("Three angles of a quadrilateral are 70°, 80° and 100°. Find the fourth.", ["360 − 250."], 110, accept=["110", "110°"]),
            _worked(
                "Which instrument is used to draw a circle?",
                ["A circle is drawn with a pair of compasses."],
                "compass",
                accept=["compass", "compasses", "a pair of compasses", "pair of compasses"],
            ),
            _worked("The angles of an equilateral triangle are equal. How large is each?", ["180 ÷ 3."], 60, accept=["60", "60°"]),
        ]
    return [
        _worked("An exterior angle is 125°. One interior opposite angle is 58°. Find the other.", ["125 − 58."], 67, accept=["67", "67°"]),
        _worked(
            "Two triangles have the same three side lengths. What word describes them?",
            ["Same size and shape means congruent."],
            "congruent",
            accept=["congruent", "congruence"],
        ),
        _worked("Two angles of a triangle are 47° and 58°. Find the third.", ["180 − 47 − 58."], 75, accept=["75", "75°"]),
    ]


def example_pythagoras(grade: int):
    a, b = (8, 15) if grade < 9 else (9, 12)
    c = int(math.hypot(a, b))
    return _worked(
        f"A right-angled triangle has shorter sides of {a} cm and {b} cm. Find the hypotenuse.",
        [f"{a}² + {b}² = {a*a} + {b*b} = {a*a + b*b}.", f"The hypotenuse is the square root of {a*a + b*b}."],
        c,
        accept=[str(c), f"{c} cm"],
    )


def practice_pythagoras(grade: int):
    return [
        _worked(
            "Shorter sides are 9 cm and 12 cm. Find the hypotenuse.",
            ["9² + 12² = 81 + 144 = 225.", "√225 = 15."],
            15,
            accept=["15", "15 cm"],
        ),
        _worked(
            "The hypotenuse is 13 cm and one shorter side is 5 cm. Find the other side.",
            ["13² − 5² = 169 − 25 = 144.", "√144 = 12."],
            12,
            accept=["12", "12 cm"],
        ),
        _worked(
            "A rectangle is 8 cm by 15 cm. How long is the diagonal?",
            ["The diagonal is the hypotenuse of a right-angled triangle.", "8² + 15² = 64 + 225 = 289.", "√289 = 17."],
            17,
            accept=["17", "17 cm"],
        ),
    ]


def example_area(grade: int):
    if grade >= 8:
        return _worked(
            "Find the area of a triangle with base 12 cm and perpendicular height 5 cm.",
            ["Area = ½ × base × height.", "½ × 12 × 5."],
            30,
            accept=["30", "30 cm^2", "30cm2"],
        )
    return _worked(
        "A rectangle is 8 cm by 5 cm. Find its area.",
        ["Area = length × breadth."],
        40,
        accept=["40", "40 cm^2", "40cm2"],
    )


def practice_area(grade: int):
    items = [
        _worked("Find the perimeter of a rectangle that is 9 cm by 4 cm.", ["Perimeter = 2 × (9 + 4)."], 26, accept=["26", "26 cm"]),
        _worked("Find the area of a rectangle that is 15 cm by 6 cm.", ["15 × 6."], 90, accept=["90", "90 cm^2"]),
    ]
    if grade >= 8:
        items.append(_worked(
            "Using π = 22/7, find the circumference of a circle with radius 7 cm.",
            ["Circumference = 2 × π × r.", "2 × 22/7 × 7 = 44."],
            44,
            accept=["44", "44 cm"],
        ))
    else:
        items.append(_worked(
            "Find the area of a triangle with base 10 cm and height 6 cm.",
            ["½ × 10 × 6."],
            30,
            accept=["30", "30 cm^2"],
        ))
    return items


def example_volume(grade: int):
    if grade >= 8:
        return _worked(
            "Using π = 22/7, find the volume of a cylinder with radius 7 cm and height 10 cm.",
            ["Volume = πr²h.", "22/7 × 49 × 10.", "22 × 7 × 10."],
            1540,
            accept=["1540", "1540 cm^3"],
        )
    return _worked(
        "Find the volume of a rectangular prism that is 5 cm by 4 cm by 3 cm.",
        ["Volume = length × breadth × height."],
        60,
        accept=["60", "60 cm^3"],
    )


def practice_volume(grade: int):
    items = [
        _worked("Find the volume of a cube with side 4 cm.", ["4 × 4 × 4."], 64, accept=["64", "64 cm^3"]),
        _worked("Find the surface area of a cube with side 3 cm.", ["Six faces, each of area 9.", "6 × 9."], 54, accept=["54", "54 cm^2"]),
    ]
    if grade >= 9:
        items.append(_worked(
            "A prism has volume 120 cm³. One dimension is doubled and the others stay the same. What is the new volume?",
            ["Multiplying one dimension by 2 multiplies the volume by 2."],
            240,
            accept=["240", "240 cm^3"],
        ))
    else:
        items.append(_worked(
            "A rectangular prism is 6 cm by 2 cm by 5 cm. Find its volume.",
            ["6 × 2 × 5."],
            60,
            accept=["60", "60 cm^3"],
        ))
    return items


def example_data(grade: int):
    if grade == 7:
        return _worked(
            "The values are 4, 7, 7, 9, 3. What is the mode?",
            ["The mode is the value that appears most often.", "7 appears twice."],
            7,
        )
    values = [14, 18, 15, 17, 21] if grade == 8 else [12, 15, 18, 15, 20]
    mean = sum(values) / len(values)
    return _worked(
        f"Find the mean of {', '.join(str(v) for v in values)}.",
        [f"Add the values: {sum(values)}.", f"Divide by {len(values)}."],
        mean,
    )


def example_probability(grade: int):
    if grade >= 9:
        return _worked(
            "A bag has 3 red counters and 2 blue counters. A counter is drawn at random. What is the probability that it is red?",
            ["There are 5 equally likely counters.", "3 of them are red.", "Simplify only if you can. 3/5 is already simplified."],
            "3/5",
            accept=["3/5", "0.6"],
        )
    if grade == 8:
        return _worked(
            "A fair die is rolled. What is the probability of getting a 6?",
            ["There are 6 equally likely outcomes.", "One of them is a 6."],
            "1/6",
            accept=["1/6"],
        )
    return _worked(
        "A fair coin is tossed. What is the probability of getting heads?",
        ["There are 2 equally likely outcomes.", "One of them is heads."],
        "1/2",
        accept=["1/2", "0.5"],
    )


def practice_probability(grade: int):
    return [
        _worked("A fair coin is tossed. What is the probability of tails?", ["One of two equally likely outcomes."], "1/2", accept=["1/2", "0.5"]),
        _worked("A fair die is rolled. What is the probability of an even number?", ["The even outcomes are 2, 4 and 6.", "3/6 = 1/2."], "1/2", accept=["1/2", "3/6", "0.5"]),
        _worked("A bag has 4 green and 1 yellow marble. What is the probability of yellow?", ["1 out of 5."], "1/5", accept=["1/5", "0.2"]),
    ]


def practice_data(grade: int):
    if grade == 7:
        return [
            _worked("The values are 2, 5, 5, 7 and 9. What is the mode?", ["5 appears more often than the others."], 5),
            _worked("The values are 2, 5, 5, 7 and 9. What is the range?", ["Range = 9 − 2."], 7),
            _worked("Find the mean of 4, 8 and 6.", ["4 + 8 + 6 = 18.", "18 ÷ 3."], 6),
        ]
    if grade == 8:
        return [
            _worked("Find the mean of 14, 18, 15, 17 and 21.", ["The sum is 85.", "85 ÷ 5."], 17),
            _worked("Find the median of 9, 3, 7, 4 and 5.", ["In order: 3, 4, 5, 7, 9."], 5),
            _worked("Find the range of 14, 18, 15, 17 and 21.", ["21 − 14."], 7),
        ]
    return [
        _worked("Find the mean of 12, 15, 18, 15 and 20.", ["The sum is 80.", "80 ÷ 5."], 16),
        _worked("Find the mode of 12, 15, 18, 15 and 20.", ["15 appears twice."], 15),
        _worked("Find the range of 12, 15, 18, 15 and 20.", ["20 − 12."], 8),
    ]


def paper_questions(grade: int, term: int) -> list[dict]:
    concepts = PLACEMENT[grade][term]
    per = 2 if len(concepts) >= 4 else 3
    questions = []
    for concept in concepts:
        for item in PRACTICE(concept)(grade)[:per]:
            questions.append({
                "concept": concept,
                "topic_id": topic_id(grade, concept),
                "topic": NAMES[concept],
                "prompt": item["prompt"],
                "memo": item["steps"],
                "accept": item["accept"],
            })
    questions = questions[:8]
    count = len(questions)
    base, extra = divmod(50, count)
    for index, question in enumerate(questions, start=1):
        question["id"] = str(index)
        question["marks"] = base + (1 if index <= extra else 0)
    return questions


def normalise_answer(value: str) -> str:
    text = value.strip().lower()
    text = text.replace("°", "").replace("degrees", "").replace("degree", "")
    text = text.replace(" ", "").replace("×", "x").replace("−", "-").replace("–", "-")
    text = text.replace("²", "^2").replace("³", "^3").replace("⁴", "^4").replace("⁵", "^5")
    text = text.replace("⁶", "^6").replace("⁷", "^7").replace("⁸", "^8").replace("⁹", "^9")
    text = text.replace("⁻", "-")
    if text.startswith("r") and len(text) > 1 and text[1].isdigit():
        text = text[1:]
    if re.fullmatch(r"-?\d+,\d+", text):
        text = text.replace(",", ".")
    else:
        text = text.replace(",", "")
    text = re.sub(r"^x=", "", text)
    text = text.replace("cm^2", "").replace("cm^3", "").replace("cm2", "").replace("cm3", "").replace("cm", "")
    return text


def answers_match(given: str, expected: list[str]) -> bool:
    left = normalise_answer(given)
    if not left:
        return False
    for item in expected:
        right = normalise_answer(item)
        if left == right:
            return True
        if _close_number(left, right):
            return True
        if re.fullmatch(r"-?\d+/\d+", right) and _close_number(left, str(_fraction_float(right))):
            return True
    return False


def _fraction_float(text: str) -> float:
    numerator, denominator = text.split("/")
    return int(numerator) / int(denominator)


def _close_number(left: str, right: str) -> bool:
    try:
        return abs(float(left) - float(right)) < 0.02
    except ValueError:
        return False


def _expand_superscripts(text: str) -> str:
    digits = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹", "0123456789")
    pieces = []
    for char in text:
        if char in "⁰¹²³⁴⁵⁶⁷⁸⁹":
            pieces.append("^" + char.translate(digits))
        else:
            pieces.append(char)
    return "".join(pieces)


def solve_question(question: str) -> dict | None:
    written = _expand_superscripts(question)
    text = " " + written.lower().replace("−", "-").replace("×", "x").replace("÷", "/") + " "
    interest = _solve_interest(text)
    if interest:
        return interest
    pythagoras = _solve_pythagoras(text)
    if pythagoras:
        return pythagoras
    percent = _solve_percent(text)
    if percent:
        return percent
    factors = _solve_factors(text)
    if factors:
        return factors
    equation = _solve_equation(question)
    if equation:
        return equation
    measure = _solve_measure(text)
    if measure:
        return measure
    chance = _solve_probability(text)
    if chance:
        return chance
    angle = _solve_angle(text)
    if angle:
        return angle
    stats = _solve_stats(text)
    if stats:
        return stats
    power = _solve_power(text)
    if power:
        return power
    fraction = _solve_fraction(text)
    if fraction:
        return fraction
    arithmetic = _solve_arithmetic(question)
    if arithmetic:
        return arithmetic
    return None


def _solve_interest(text: str) -> dict | None:
    if "simple interest" not in text and "compound interest" not in text:
        return None
    rate_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%", text)
    year_match = re.search(r"(\d+)\s*years?", text)
    principal_match = re.search(r"r\s*(\d[\d\s]*)", text)
    if not (rate_match and year_match and principal_match):
        return None
    rate = float(rate_match.group(1).replace(",", "."))
    years = int(year_match.group(1))
    principal = float(principal_match.group(1).replace(" ", ""))
    if "compound interest" in text and years <= 4:
        amount = principal
        steps = [f"Start with {_money(principal)}."]
        for year in range(1, years + 1):
            interest = amount * rate / 100
            amount += interest
            steps.append(f"Year {year}: interest {_money(interest)}, amount {_money(round(amount, 2))}.")
        return {"concept": "finance", "steps": steps, "answer": f"{amount:.2f}", "accept": [f"{amount:.2f}", _money(round(amount, 2))]}
    interest = principal * years * rate / 100
    return {
        "concept": "finance",
        "steps": [
            "The curriculum formula is SI = P × n × r / 100.",
            f"P = {_money(principal)}, n = {years}, r = {rate}.",
            f"SI = { _num(principal)} × {years} × {_num(rate)} / 100.",
        ],
        "answer": _num(interest),
        "accept": [_num(interest), _money(interest)],
    }


def _solve_pythagoras(text: str) -> dict | None:
    if not any(word in text for word in ("pythag", "hypotenuse", "right-angled", "right angled")):
        return None
    numbers = [float(item) for item in re.findall(r"\d+(?:[.,]\d+)?", text)]
    numbers = [int(item) if item.is_integer() else item for item in numbers]
    if len(numbers) < 2:
        return None
    a, b = numbers[0], numbers[1]
    if "other side" in text or "remaining" in text or "shorter side" in text and "hypotenuse is" in text:
        longer, shorter = max(a, b), min(a, b)
        value = math.sqrt(longer ** 2 - shorter ** 2)
        return {
            "concept": "pythagoras",
            "steps": [
                "The hypotenuse is the longest side.",
                f"Subtract the known square: { _num(longer)}² − {_num(shorter)}² = {_num(longer**2 - shorter**2)}.",
                "The missing side is the square root of that result.",
            ],
            "answer": _num(value),
            "accept": [_num(value)],
        }
    value = math.sqrt(a ** 2 + b ** 2)
    return {
        "concept": "pythagoras",
        "steps": [
            "The hypotenuse is opposite the right angle.",
            f"{_num(a)}² + {_num(b)}² = {_num(a**2)} + {_num(b**2)} = {_num(a**2 + b**2)}.",
            "The hypotenuse is the square root of that sum.",
        ],
        "answer": _num(value),
        "accept": [_num(value)],
    }


def _solve_percent(text: str) -> dict | None:
    of_match = re.search(r"(\d+(?:[.,]\d+)?)\s*%\s*of\s+r?\s*(\d[\d\s]*(?:[.,]\d+)?)", text)
    if of_match and "increase" not in text and "decrease" not in text and "reduced" not in text:
        rate = float(of_match.group(1).replace(",", "."))
        amount = float(of_match.group(2).replace(" ", "").replace(",", "."))
        value = amount * rate / 100
        return {
            "concept": "fractions",
            "steps": [
                f"{_num(rate)}% means {_num(rate)}/100.",
                f"Multiply {_num(amount)} by {_num(rate)}/100.",
            ],
            "answer": _num(value),
            "accept": [_num(value), _money(value)],
        }
    change = re.search(r"(increase|decrease|reduced|reduce)\s+r?\s*(\d[\d\s]*)\s+by\s+(\d+(?:[.,]\d+)?)\s*%", text)
    if change:
        direction, amount_text, rate_text = change.groups()
        amount = float(amount_text.replace(" ", ""))
        rate = float(rate_text.replace(",", "."))
        delta = amount * rate / 100
        value = amount + delta if direction == "increase" else amount - delta
        verb = "Add" if direction == "increase" else "Subtract"
        return {
            "concept": "fractions",
            "steps": [
                f"{_num(rate)}% of {_num(amount)} is {_num(delta)}.",
                f"{verb} that change.",
            ],
            "answer": _num(value),
            "accept": [_num(value), _money(value)],
        }
    return None


def _solve_factors(text: str) -> dict | None:
    match = re.search(r"\b(hcf|lcm|highest common factor|lowest common multiple)\b.{0,40}?(\d+)\s+and\s+(\d+)", text)
    if not match:
        return None
    kind, left, right = match.group(1), int(match.group(2)), int(match.group(3))
    hcf = math.gcd(left, right)
    if kind in ("hcf", "highest common factor"):
        return {
            "concept": "whole_numbers",
            "steps": [
                f"Find the factors shared by {left} and {right}.",
                "The highest of those common factors is the HCF.",
            ],
            "answer": str(hcf),
            "accept": [str(hcf)],
        }
    lcm = abs(left * right) // hcf
    return {
        "concept": "whole_numbers",
        "steps": [
            f"The HCF of {left} and {right} is {hcf}.",
            "LCM = product ÷ HCF.",
        ],
        "answer": str(lcm),
        "accept": [str(lcm)],
    }


def _solve_equation(question: str) -> dict | None:
    compact = question.lower().replace(" ", "").replace("−", "-")
    if "x" not in compact:
        return None
    bracket = re.fullmatch(r".*?(-?\d*)\(x([+-]\d+)\)=(-?\d+).*", compact)
    if bracket:
        coeff_text, inner, result_text = bracket.groups()
        coeff = int(coeff_text) if coeff_text not in ("", "+", "-") else (-1 if coeff_text == "-" else 1)
        result = int(result_text)
        inner_value = result / coeff
        constant = int(inner)
        value = inner_value - constant
        if abs(value - round(value)) > 1e-9:
            return None
        return {
            "concept": "equations",
            "steps": [
                f"Divide both sides by {coeff}.",
                f"x {inner} = {_num(inner_value)}.",
                "Undo the constant by doing the opposite operation to both sides.",
            ],
            "answer": _num(value),
            "accept": [_num(value), f"x={_num(value)}"],
        }
    linear = re.search(r"(-?\d*)x([+-]\d+)?=(-?\d+)", compact)
    if linear and "x^" not in compact and "x2" not in compact:
        coeff_text, constant_text, result_text = linear.groups()
        coeff = int(coeff_text) if coeff_text not in ("", "+", "-") else (-1 if coeff_text == "-" else 1)
        constant = int(constant_text) if constant_text else 0
        result = int(result_text)
        if coeff == 0:
            return None
        value = (result - constant) / coeff
        if abs(value - round(value)) > 1e-9:
            return None
        steps = []
        if constant:
            steps.append(f"Move the constant by doing the opposite operation on both sides. {coeff}x = {result - constant}.")
        steps.append(f"Divide both sides by {coeff}.")
        return {
            "concept": "equations",
            "steps": steps,
            "answer": _num(round(value)),
            "accept": [_num(round(value)), f"x={_num(round(value))}"],
        }
    return None


def _solve_measure(text: str) -> dict | None:
    rectangle = re.search(r"rectangle.{0,50}?(\d+(?:[.,]\d+)?)\s*(?:cm|m|mm)?\s*(?:by|x)\s*(\d+(?:[.,]\d+)?)", text)
    if rectangle and "diagonal" not in text:
        length = float(rectangle.group(1))
        breadth = float(rectangle.group(2))
        if "perimeter" in text:
            value = 2 * (length + breadth)
            steps = [f"Perimeter = 2 × ({_num(length)} + {_num(breadth)})."]
        else:
            value = length * breadth
            steps = [f"Area = length × breadth = {_num(length)} × {_num(breadth)}."]
        return {"concept": "area", "steps": steps, "answer": _num(value), "accept": [_num(value)]}
    triangle = re.search(r"triangle.{0,80}?base\s*(\d+(?:[.,]\d+)?).{0,40}?height\s*(\d+(?:[.,]\d+)?)", text)
    if triangle and "area" in text:
        base, height = float(triangle.group(1)), float(triangle.group(2))
        value = 0.5 * base * height
        return {
            "concept": "area",
            "steps": [f"Area = ½ × {_num(base)} × {_num(height)}."],
            "answer": _num(value),
            "accept": [_num(value)],
        }
    prism = re.search(r"(?:prism|cuboid).{0,40}?(\d+)\s*(?:cm)?\s*(?:by|x)\s*(\d+)\s*(?:cm)?\s*(?:by|x)\s*(\d+)", text)
    if prism and "volume" in text:
        a, b, c = (int(prism.group(i)) for i in (1, 2, 3))
        return {
            "concept": "volume",
            "steps": [f"Volume = {a} × {b} × {c}."],
            "answer": str(a * b * c),
            "accept": [str(a * b * c)],
        }
    return None


def _solve_probability(text: str) -> dict | None:
    if "probability" not in text:
        return None
    if "coin" in text:
        return {"concept": "probability", "steps": ["A fair coin has 2 equally likely outcomes.", "One of them is favourable."], "answer": "1/2", "accept": ["1/2", "0.5"]}
    if "even" in text and ("die" in text or "dice" in text):
        return {"concept": "probability", "steps": ["The even faces are 2, 4 and 6.", "3 outcomes out of 6 is 1/2."], "answer": "1/2", "accept": ["1/2", "3/6", "0.5"]}
    if "die" in text or "dice" in text:
        return {"concept": "probability", "steps": ["A fair die has 6 equally likely faces.", "One face matches the event."], "answer": "1/6", "accept": ["1/6"]}
    return None


def _solve_angle(text: str) -> dict | None:
    if "angle" not in text and "°" not in text:
        return None
    numbers = [int(float(item)) for item in re.findall(r"\d+", text) if float(item) <= 180]
    if not numbers:
        return None
    if "straight line" in text or "adjacent" in text:
        value = 180 - numbers[0]
        return {"concept": "straight_lines", "steps": ["Adjacent angles on a straight line add to 180°.", f"180 − {numbers[0]}."], "answer": str(value), "accept": [str(value), f"{value}°"]}
    if "co-interior" in text:
        value = 180 - numbers[0]
        return {"concept": "straight_lines", "steps": ["Co-interior angles add to 180°.", f"180 − {numbers[0]}."], "answer": str(value), "accept": [str(value), f"{value}°"]}
    if "vertically opposite" in text or "corresponding" in text or "alternate" in text:
        return {"concept": "straight_lines", "steps": ["This pair of angles is equal."], "answer": str(numbers[0]), "accept": [str(numbers[0]), f"{numbers[0]}°"]}
    return None


def _solve_stats(text: str) -> dict | None:
    kind = None
    for word in ("mean", "average", "median", "mode", "range"):
        if re.search(rf"\b{word}\b", text):
            kind = "data" if word != "average" else "data"
            which = "mean" if word == "average" else word
            break
    else:
        return None
    if which != "mean" and which != "median" and which != "mode" and which != "range":
        return None
    numbers = [float(item) for item in re.findall(r"\d+(?:[.,]\d+)?", text)]
    if len(numbers) < 2:
        return None
    if which == "mean":
        value = sum(numbers) / len(numbers)
        return {"concept": "data", "steps": [f"Add the values to get {_num(sum(numbers))}.", f"Divide by {len(numbers)}."], "answer": _num(value), "accept": [_num(value)]}
    if which == "range":
        value = max(numbers) - min(numbers)
        return {"concept": "data", "steps": [f"Range = highest − lowest = {_num(max(numbers))} − {_num(min(numbers))}."], "answer": _num(value), "accept": [_num(value)]}
    ordered = sorted(numbers)
    if which == "median" and len(ordered) % 2 == 1:
        value = ordered[len(ordered) // 2]
        return {"concept": "data", "steps": ["Order the values first.", "The median is the middle value."], "answer": _num(value), "accept": [_num(value)]}
    return None


def _solve_power(text: str) -> dict | None:
    product = re.search(r"(\d+)\s*(?:\^|to the power(?: of)?)\s*(\d+)\s*[x*]\s*(\d+)\s*(?:\^|to the power(?: of)?)\s*(\d+)", text)
    if product:
        base_a, exp_a, base_b, exp_b = (int(item) for item in product.groups())
        if base_a == base_b:
            value = base_a ** (exp_a + exp_b)
            return {
                "concept": "exponents",
                "steps": [
                    "The bases are the same, so add the exponents.",
                    f"{base_a}^{exp_a + exp_b} = {value}.",
                ],
                "answer": str(value),
                "accept": [str(value), f"{base_a}^{exp_a + exp_b}"],
            }
    single = re.search(r"(\d+)\s*(?:\^|to the power(?: of)?)\s*(\d+)", text)
    if single and "pattern" not in text:
        base, exp = int(single.group(1)), int(single.group(2))
        if exp <= 12:
            return {
                "concept": "exponents",
                "steps": [f"{base}^{exp} means {exp} factors of {base}."],
                "answer": str(base ** exp),
                "accept": [str(base ** exp), f"{base}^{exp}"],
            }
    root = re.search(r"square root of\s+(\d+)", text)
    if root:
        number = int(root.group(1))
        root_value = math.isqrt(number)
        if root_value * root_value == number:
            return {"concept": "exponents", "steps": [f"Find the whole number which multiplies by itself to give {number}."], "answer": str(root_value), "accept": [str(root_value)]}
    return None


def _solve_fraction(text: str) -> dict | None:
    added = re.search(r"(\d+)\s*/\s*(\d+)\s*\+\s*(\d+)\s*/\s*(\d+)", text)
    if added:
        left = Fraction(int(added.group(1)), int(added.group(2)))
        right = Fraction(int(added.group(3)), int(added.group(4)))
        total = left + right
        answer = f"{total.numerator}/{total.denominator}" if total.denominator != 1 else str(total.numerator)
        return {
            "concept": "fractions",
            "steps": [
                f"The common denominator is {math.lcm(left.denominator, right.denominator)}.",
                "Rewrite both fractions, then add the numerators.",
            ],
            "answer": answer,
            "accept": [answer],
        }
    return None


def _solve_arithmetic(question: str) -> dict | None:
    original = question.strip()
    text = original.lower().strip().rstrip("?.!")
    text = re.sub(
        r"^(please\s+)?(can you\s+)?(calculate|what is|what's|whats|find|evaluate|simplify|work out|solve|compute)\s+",
        "",
        text,
    )
    text = re.sub(r"^(the\s+)?(sum|total|product|difference|quotient)\s+of\s+", "", text)
    text = re.sub(r"^(add|addition|plus|sum)\s+", "", text)
    text = text.replace("×", "*").replace("÷", "/").replace("−", "-").replace("–", "-")
    text = re.sub(r"(\d)\s*x\s*(\d)", r"\1*\2", text)
    text = text.replace("^", "**")
    text = re.sub(r"\b(plus|added to)\b", "+", text)
    text = re.sub(r"\b(minus|take away)\b", "-", text)
    text = re.sub(r"\b(times|multiplied by)\b", "*", text)
    text = re.sub(r"\b(divided by)\b", "/", text)
    text = re.sub(r"(\d)\s+and\s+(\d)", r"\1+\2", text)
    text = re.sub(r"\s+", " ", text).strip()
    if not re.fullmatch(r"[\d\.\+\-\*\/\(\)\s]+", text):
        return None
    if not re.search(r"\d", text):
        return None
    try:
        value = _safe_number(text)
    except Exception:
        return None
    concept = "integers" if re.search(r"(^|[\+\-\*/\(])\s*-\d", text) or value < 0 else "whole_numbers"
    return {
        "concept": concept,
        "prompt": original,
        "steps": _arithmetic_steps(text, value),
        "answer": _num(value),
        "accept": [_num(value)],
    }


def _arithmetic_steps(expression: str, value) -> list[str]:
    simple = re.fullmatch(r"\s*(-?\d+(?:\.\d+)?)\s*([+\-*/])\s*(-?\d+(?:\.\d+)?)\s*", expression)
    if simple:
        left, operator, right = simple.groups()
        action = {"+": "Add", "-": "Subtract", "*": "Multiply", "/": "Divide"}[operator]
        shown = operator if operator != "*" else "×"
        return [f"{action} the numbers.", f"{left} {shown} {right} = {_num(value)}."]
    return [
        "Follow the order of operations: brackets, then multiplication and division, then addition and subtraction.",
        f"The value is {_num(value)}.",
    ]


def _safe_number(expression: str):
    tree = ast.parse(expression, mode="eval")
    allowed = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.USub, ast.UAdd, ast.FloorDiv, ast.Mod,
    )
    for node in ast.walk(tree):
        if not isinstance(node, allowed):
            raise ValueError("unsupported")
        if isinstance(node, ast.Constant) and not isinstance(node.value, (int, float)):
            raise ValueError("unsupported")
    return eval(compile(tree, "<expr>", "eval"), {"__builtins__": {}}, {})


def self_check():
    interest = solve_question("Calculate the simple interest on R2000 at 8% per year for 3 years.")
    assert interest and interest["answer"] == "480", interest
    hypot = solve_question("Find the hypotenuse of a right-angled triangle with sides 6 cm and 8 cm.")
    assert hypot and hypot["answer"] == "10", hypot
    hcf = solve_question("Find the HCF of 36 and 48.")
    assert hcf and hcf["answer"] == "12", hcf
    equation = solve_question("Solve 3x + 5 = 20")
    assert equation and equation["answer"] == "5", equation
    fraction = solve_question("Calculate 1/2 + 1/3")
    assert fraction and fraction["answer"] == "5/6", fraction
    power = solve_question("Calculate 2^3 x 2^4")
    assert power and power["answer"] == "128", power
    topic = classify("What is the additive inverse, and calculate -8 + 5 x -2", 8)
    assert topic["concept"] == "integers", topic
    finance = classify("Calculate the simple interest on R600 at 7% per year for 3 years", 9)
    assert finance["concept"] == "finance", finance
    for grade in (7, 8, 9):
        for term in (1, 2, 3, 4):
            questions = paper_questions(grade, term)
            assert questions, (grade, term)
            assert sum(item["marks"] for item in questions) == 50, (grade, term, questions)
            for item in questions:
                assert answers_match(item["accept"][0], item["accept"])
    assert answers_match("R480", ["480"])
    assert answers_match("5/6", ["5/6"])
    assert answers_match("x = 5", ["5"])
    print("curriculum self-check passed")


if __name__ == "__main__":
    self_check()
