"""The one place drink categories are defined.

Run `python3 scripts/drinks.py` after editing to regenerate the issue templates.
"""
import json
from pathlib import Path

# Each category: detail fields (label, placeholder), the first one required,
# and six flavour axes (label, hint) scored 0-5 for the radar chart.
CATEGORIES = [
    {
        "key": "beer", "name": "Beer", "colour": "#e2bf55",
        "blurb": "Taps, cans and the odd bottle carried home from a trip.",
        "fields": [("Brewery", "Guinness"), ("Style", "Irish stout, West Coast IPA, saison"),
                   ("ABV", "4.2%"), ("Origin", "Dublin, Ireland")],
        "axes": [("Bitter", "Hop bitterness, mostly on the finish"),
                 ("Hoppy", "Citrus, pine, tropical or grassy hop aroma"),
                 ("Malty", "Bread, biscuit, caramel"),
                 ("Roasty", "Coffee, dark chocolate, burnt toast"),
                 ("Fruity", "Yeast esters: banana, stone fruit, berries"),
                 ("Sour", "Tart, acidic or funky")],
        "link_hint": "Untappd page for this beer",
    },
    {
        "key": "whiskey", "name": "Whiskey", "colour": "#cf7f3e",
        "blurb": "The top shelf. Scotch, bourbon, rye and everything in between.",
        "fields": [("Distillery", "Lagavulin"), ("Style", "Single malt Scotch, bourbon, rye"),
                   ("Age", "16 years"), ("ABV", "43%"), ("Region", "Islay, Scotland")],
        "axes": [("Sweet", "Vanilla, honey, toffee"),
                 ("Fruity", "Apple, citrus, dried fruit"),
                 ("Floral", "Heather, grass, blossom"),
                 ("Spicy", "Pepper, cinnamon, clove"),
                 ("Oak", "Wood, tannin, char"),
                 ("Peaty", "Smoke, iodine, campfire")],
        "link_hint": "Whiskybase page for this bottling",
    },
    {
        "key": "gin", "name": "Gin", "colour": "#93aedc",
        "blurb": "Juniper first, then whatever the distiller had in mind.",
        "fields": [("Distillery", "Four Pillars"), ("Style", "London dry, Old Tom, contemporary"),
                   ("ABV", "41.8%"), ("Origin", "Yarra Valley, Australia")],
        "axes": [("Juniper", "Pine, resin, the classic gin backbone"),
                 ("Citrus", "Lemon, orange, grapefruit peel"),
                 ("Floral", "Rose, lavender, elderflower"),
                 ("Herbal", "Coriander, sage, tea"),
                 ("Spice", "Cardamom, pepper, cassia"),
                 ("Earthy", "Angelica, orris root, nuts")],
        "link_hint": "The distillery's page for this gin",
    },
    {
        "key": "other-spirits", "name": "Other spirits", "colour": "#b98ac0",
        "blurb": "Rum, tequila, brandy, mezcal: everything without a shelf of its own.",
        "fields": [("Producer", "Del Maguey"), ("Spirit", "Rum, tequila, cognac, mezcal"),
                   ("Age", "Joven, 8 years, VSOP"), ("ABV", "40%"), ("Origin", "Oaxaca, Mexico")],
        "axes": [("Sweet", "Sugar, molasses, honey"),
                 ("Fruity", "Tropical, stone or dried fruit"),
                 ("Herbal", "Grass, agave, green notes"),
                 ("Spicy", "Pepper, baking spice"),
                 ("Woody", "Barrel, vanilla, tannin"),
                 ("Smoky", "Smoke, ash, roast")],
        "link_hint": "Producer or review page for this bottle",
    },
    {
        "key": "cocktails", "name": "Cocktails", "colour": "#b5d67a",
        "blurb": "Mixed drinks, with what went into them and how.",
        "fields": [("Where", "The bar, or home, and who made it"), ("Base spirit", "Gin, rye, mezcal")],
        "axes": [("Sweet", "Sugar, syrups, liqueurs"),
                 ("Sour", "Citrus, acidity"),
                 ("Bitter", "Amaro, bitters, Campari"),
                 ("Boozy", "How strongly the spirit comes through"),
                 ("Herbal", "Vermouth, chartreuse, fresh herbs"),
                 ("Fruity", "Fruit juice, fruit liqueur, garnish")],
        "link_hint": "Recipe page, e.g. on Difford's Guide",
        "recipe": True,
    },
    {
        "key": "wine", "name": "Wine", "colour": "#d0566f",
        "blurb": "For the evenings that called for a glass instead.",
        "fields": [("Producer", "Penfolds"), ("Grape", "Shiraz, or the blend"),
                   ("Vintage", "2019"), ("Region", "Barossa Valley, Australia"),
                   ("Style", "Red, white, rosé, sparkling, fortified")],
        "axes": [("Sweetness", "Dry at 0, lusciously sweet at 5"),
                 ("Acidity", "Mouth-watering freshness"),
                 ("Tannin", "Drying grip on the gums (mostly reds)"),
                 ("Alcohol", "Warmth in the throat"),
                 ("Body", "Light like water, or heavy like cream"),
                 ("Finish", "How long the flavour lingers")],
        "link_hint": "Vivino page for this wine",
    },
]

RATINGS = ["1 - not for me", "2 - fine", "3 - good", "4 - very good", "5 - outstanding"]


def template(cat):
    """Issue form YAML. JSON-encoded scalars are valid YAML and need no escaping rules."""
    q = json.dumps
    out = [f"name: {q(cat['name'])}",
           f"description: {q('Log a ' + cat['name'].lower().rstrip('s') + ' you have tried.')}",
           f"labels: [{q(cat['key'])}]",
           "body:"]

    def block(kind, label, required=False, **attrs):
        out.append(f"  - type: {kind}")
        out.append("    attributes:")
        out.append(f"      label: {q(label)}")
        out.extend(f"      {k}: {q(v)}" for k, v in attrs.items())
        out.append(f"    validations:\n      required: {str(required).lower()}")

    for n, (label, placeholder) in enumerate(cat["fields"]):
        block("input", label, required=n == 0, placeholder=placeholder)
    out.append('  - type: markdown\n    attributes:\n      value: "### Flavour profile\\n0 means absent, 5 means it dominates."')
    for label, hint in cat["axes"]:
        block("dropdown", label, required=True, description=hint, options=[str(n) for n in range(6)])
    block("dropdown", "Rating", required=True, options=RATINGS)
    if cat.get("recipe"):
        block("textarea", "Ingredients", required=True, placeholder="- 60 ml rye\n- 30 ml sweet vermouth\n- 2 dashes Angostura")
        block("textarea", "Method", required=True, placeholder="Stir with ice, strain into a chilled coupe, garnish with a cherry.")
    block("textarea", "Tasting notes", required=True,
          placeholder="Where you were, who recommended it, nose, palate, finish...")
    block("textarea", "Photo", description="Optional. Drag an image in here; it goes at the top of the page.")
    block("input", "Link", description=f"Optional. {cat['link_hint']}.", placeholder="https://")
    return "\n".join(out) + "\n"


if __name__ == "__main__":
    folder = Path(__file__).resolve().parent.parent / ".github" / "ISSUE_TEMPLATE"
    folder.mkdir(parents=True, exist_ok=True)
    for i, cat in enumerate(CATEGORIES, 1):
        # Numbered so the issue chooser keeps the category order.
        (folder / f"{i}-{cat['key']}.yml").write_text(template(cat))
    print(f"Wrote {len(CATEGORIES)} templates to {folder}")
