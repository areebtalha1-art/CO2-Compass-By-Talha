import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Carbon Compass | CO2 calculator",
    page_icon=":material/eco:",
    layout="wide",
    initial_sidebar_state="collapsed",
)

GRID_TCO2_PER_MWH = 0.40
FUEL_TCO2_PER_GJ = 0.0561
AGRICULTURE_DIESEL_KG_PER_LITRE = 2.68
AGRICULTURE_SOIL_KG_PER_KG_N = 4.3
AGRICULTURE_METHANE_GWP100 = 27.2
RICE_METHANE_KG_PER_HA_DAY = 1.19
RICE_FLOODED_DAYS_PER_SEASON = 120
CATTLE_ENTERIC_METHANE_KG_PER_HEAD_YEAR = 60.0
CATTLE_MANURE_METHANE_KG_PER_HEAD_YEAR = 5.0
PERSONAL_REFERENCE_TCO2 = 2.19
PERSONAL_REFERENCE_YEAR = 2025
PERSONAL_GRID_KG_PER_KWH = 0.716
PERSONAL_PETROL_KG_PER_LITRE = 2.31
PERSONAL_DIESEL_KG_PER_LITRE = 2.68
PERSONAL_CNG_KG_PER_KG = 2.75
PERSONAL_TRANSIT_KG_PER_KM = 0.050
PERSONAL_LPG_TCO2_PER_CYLINDER = 0.0426
PERSONAL_DOMESTIC_FLIGHT_TONNES = 0.15
PERSONAL_INTERNATIONAL_FLIGHT_TONNES = 0.75
DIET_FOOTPRINTS = {
    "Mostly plant-based": 1.0,
    "Mixed diet": 1.5,
    "Meat-inclusive diet": 2.2,
}
CALCULATOR_CHOICES = {
    "industry": (
        ("Sugarcane processing", "Cane throughput, boiler energy, and process emissions.", "red"),
        ("General manufacturing", "Factory electricity, fuel, and product output.", "blue"),
        ("Oil refining", "Crude throughput, refinery fuel, flaring, and process sources.", "orange"),
        ("Cement production", "Kiln energy and limestone calcination emissions.", "amber"),
        ("Steel production", "Steel output, furnace energy, and reducing-agent emissions.", "violet"),
    ),
    "agriculture": (
        ("Crop farming", "Crop output, nitrogen fertilizer, diesel, and purchased electricity.", "lime"),
        ("Rice cultivation", "Rice area, growing season, methane, fertilizer, and farm energy.", "blue"),
        ("Dairy & cattle", "Herd size, enteric and manure methane, and milk or livestock output.", "orange"),
        ("Poultry farming", "Poultry output, manure emissions, and farm energy.", "rainbow"),
    ),
    "ammonia": (
        ("Natural gas (grey hydrogen)", "Fossil-based hydrogen; the starting factor is 10 kg CO2e/kg H2.", "blue"),
        ("Coal (high-carbon hydrogen)", "Coal gasification has a higher illustrative hydrogen factor.", "orange"),
        ("Renewable electricity (green hydrogen)", "Electrolysis powered by renewables; lifecycle emissions still vary.", "lime"),
    ),
}
HYDROGEN_FACTORS = {
    "Natural gas (grey hydrogen)": 10.0,
    "Coal (high-carbon hydrogen)": 20.0,
    "Renewable electricity (green hydrogen)": 1.5,
}
INDUSTRIES = {
    "Sugarcane processing": {
        "activity_label": "Sugarcane processed (tonnes per year)",
        "fuel_label": "Boiler and process fuel (GJ per year)",
        "process_label": "Other direct emissions (tonnes CO2e per year)",
        "reference": 0.12,
        "reference_unit": "t CO2e / t cane",
        "suggestions": (
            "Use bagasse to supply process heat and electricity.",
            "Improve boiler efficiency and reduce steam losses.",
            "Recover heat from juice clarification and evaporation.",
        ),
    },
    "General manufacturing": {
        "activity_label": "Manufactured product (tonnes per year)",
        "fuel_label": "Manufacturing fuel use (GJ per year)",
        "process_label": "Process and refrigerant emissions (tonnes CO2e per year)",
        "reference": 0.75,
        "reference_unit": "t CO2e / t product",
        "suggestions": (
            "Measure energy use by production line and remove idle loads.",
            "Electrify low-temperature heat where practical.",
            "Reduce scrap and improve material yield.",
        ),
    },
    "Oil refining": {
        "activity_label": "Crude oil throughput (tonnes per year)",
        "fuel_label": "Refinery fuel use (GJ per year)",
        "process_label": "Process, flaring, and fugitive emissions (tonnes CO2e per year)",
        "reference": 0.25,
        "reference_unit": "t CO2e / t crude throughput",
        "suggestions": (
            "Improve furnace efficiency and recover waste heat.",
            "Reduce flaring, steam leaks, and methane losses.",
            "Use process integration to lower hydrogen and heat demand.",
        ),
    },
    "Cement production": {
        "activity_label": "Cement produced (tonnes per year)",
        "fuel_label": "Kiln and process fuel use (GJ per year)",
        "process_label": "Limestone calcination and other process emissions (tonnes CO2e per year)",
        "reference": 0.85,
        "reference_unit": "t CO2e / t cement",
        "suggestions": (
            "Use supplementary cementitious materials to reduce clinker.",
            "Improve kiln efficiency and switch to lower-carbon fuels.",
            "Consider carbon capture for unavoidable process emissions.",
        ),
    },
    "Steel production": {
        "activity_label": "Crude steel output (tonnes per year)",
        "fuel_label": "Furnace and process fuel use (GJ per year)",
        "process_label": "Process and reducing-agent emissions (tonnes CO2e per year)",
        "reference": 1.90,
        "reference_unit": "t CO2e / t steel",
        "suggestions": (
            "Increase scrap-based electric-arc-furnace production.",
            "Improve furnace heat recovery and use cleaner electricity.",
            "Evaluate low-carbon hydrogen for ironmaking where suitable.",
        ),
    },
}
GLOBAL_CO2_YEARS = list(range(1979, 2026))
GLOBAL_CO2_PPM = [
    336.85, 338.91, 340.11, 340.85, 342.53, 344.07, 345.54, 346.97, 348.68,
    351.16, 352.79, 354.06, 355.40, 356.09, 356.84, 358.33, 360.18, 361.93,
    363.04, 365.70, 367.79, 368.96, 370.57, 372.58, 375.14, 376.95, 378.98,
    381.15, 382.90, 385.02, 386.50, 388.75, 390.62, 392.65, 395.40, 397.34,
    399.65, 403.07, 405.22, 407.61, 410.07, 412.45, 414.70, 417.08, 419.35,
    422.79, 425.62,
]
IPCC_2019_SECTOR_SHARES = pd.DataFrame(
    {
        "Sector": [
            "Energy supply",
            "Industry",
            "Agriculture, forestry and other land use",
            "Transport",
            "Buildings",
        ],
        "Share of global emissions (%)": [34, 24, 22, 15, 6],
    }
)

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(ellipse at 10% 0%, rgba(0, 245, 180, .09), transparent 34%),
            radial-gradient(ellipse at 92% 18%, rgba(0, 190, 255, .08), transparent 32%),
            #070a0d;
    }
    .block-container { padding-top: 2rem; padding-bottom: 3rem; }
    [data-testid="stHeader"] { background: rgba(7, 10, 13, .78); }
    .hero {
        padding: 2.4rem 2.6rem;
        margin: .5rem 0 1.7rem;
        border: 1px solid rgba(0, 255, 190, .32);
        border-radius: 24px;
        background: linear-gradient(120deg, rgba(0, 255, 190, .09), rgba(0, 190, 255, .035) 55%, rgba(7, 10, 13, .7));
        box-shadow: 0 0 38px rgba(0, 255, 190, .10), inset 0 0 28px rgba(0, 255, 190, .025);
    }
    .eyebrow {
        color: #72f8cf;
        font-size: .78rem;
        font-weight: 700;
        letter-spacing: .19em;
        text-transform: uppercase;
    }
    .hero-title {
        color: #f3fffb;
        font-size: clamp(2.2rem, 5vw, 4.3rem);
        line-height: 1.02;
        font-weight: 800;
        margin: .55rem 0 .85rem;
        text-shadow: 0 0 26px rgba(0, 255, 190, .16);
    }
    .hero-copy { color: #b7c8c4; font-size: 1.05rem; max-width: 760px; }
    .neon-card {
        min-height: 208px;
        padding: 1.35rem 1.45rem;
        border: 1px solid rgba(160, 185, 190, .24);
        border-radius: 18px;
        background: linear-gradient(145deg, rgba(16, 25, 28, .96), rgba(10, 15, 19, .98));
        box-shadow: 0 0 18px rgba(140, 180, 190, .07);
        transition: border-color .2s ease, box-shadow .2s ease;
    }
    .neon-card h3 { margin: .25rem 0 .75rem; color: #f2fbff; font-size: 1.22rem; }
    .neon-card p { color: #c1cfce; font-size: 1rem; line-height: 1.72; margin: 0 0 .8rem; }
    .neon-card p:last-child { margin-bottom: 0; }
    .neon-card--green { border-color: rgba(0, 255, 170, .52); box-shadow: 0 0 24px rgba(0, 255, 170, .13), inset 0 0 22px rgba(0, 255, 170, .035); }
    .neon-card--blue { border-color: rgba(63, 165, 255, .56); box-shadow: 0 0 24px rgba(63, 165, 255, .14), inset 0 0 22px rgba(63, 165, 255, .04); }
    .neon-card--red { border-color: rgba(255, 78, 105, .58); box-shadow: 0 0 24px rgba(255, 78, 105, .14), inset 0 0 22px rgba(255, 78, 105, .035); }
    .neon-card--violet { border-color: rgba(183, 109, 255, .58); box-shadow: 0 0 24px rgba(183, 109, 255, .14), inset 0 0 22px rgba(183, 109, 255, .035); }
    .neon-card--amber { border-color: rgba(255, 184, 61, .58); box-shadow: 0 0 24px rgba(255, 184, 61, .13), inset 0 0 22px rgba(255, 184, 61, .035); }
    .neon-card--cyan { border-color: rgba(45, 229, 230, .58); box-shadow: 0 0 24px rgba(45, 229, 230, .13), inset 0 0 22px rgba(45, 229, 230, .035); }
    .neon-card--pink { border-color: rgba(255, 100, 207, .58); box-shadow: 0 0 24px rgba(255, 100, 207, .13), inset 0 0 22px rgba(255, 100, 207, .035); }
    .neon-card--rainbow {
        border-color: rgba(200, 150, 255, .62);
        background: linear-gradient(140deg, rgba(255, 75, 120, .08), rgba(112, 82, 255, .08) 48%, rgba(0, 225, 210, .08)), #0b1115;
        box-shadow: 0 0 26px rgba(255, 90, 150, .12), 0 0 42px rgba(80, 140, 255, .08), inset 0 0 26px rgba(0, 240, 210, .04);
    }
    .neon-card--orange { border-color: rgba(255, 145, 54, .62); box-shadow: 0 0 24px rgba(255, 145, 54, .16), inset 0 0 22px rgba(255, 145, 54, .04); }
    .neon-card--lime { border-color: rgba(184, 255, 68, .58); box-shadow: 0 0 24px rgba(184, 255, 68, .14), inset 0 0 22px rgba(184, 255, 68, .035); }
    .card-kicker { color: #d7e8e5; font-size: .76rem; letter-spacing: .13em; text-transform: uppercase; }
    .neon-card--green .card-kicker { color: #63ffd0; }
    .neon-card--blue .card-kicker { color: #83c8ff; }
    .neon-card--red .card-kicker { color: #ff9aa9; }
    .neon-card--violet .card-kicker { color: #d3a6ff; }
    .neon-card--amber .card-kicker { color: #ffd27b; }
    .neon-card--cyan .card-kicker { color: #78ffff; }
    .neon-card--pink .card-kicker { color: #ff9de1; }
    .neon-card--orange .card-kicker { color: #ffc184; }
    .neon-card--lime .card-kicker { color: #d3ff8c; }
    .choice-card { min-height: 190px; }
    .choice-card--selected { transform: translateY(-2px); outline: 1px solid currentColor; }
    .result-panel {
        border: 1px solid rgba(200, 150, 255, .65);
        border-radius: 18px;
        padding: 1.1rem 1.25rem;
        background: linear-gradient(145deg, rgba(255, 90, 150, .07), rgba(90, 100, 255, .07) 52%, rgba(0, 235, 210, .07)), rgba(12, 19, 22, .9);
        box-shadow: 0 0 26px rgba(255, 90, 150, .12), 0 0 35px rgba(80, 140, 255, .08), inset 0 0 22px rgba(0, 240, 210, .04);
        margin: .8rem 0 1rem;
    }
    .result-label { color: #8ca39d; font-size: .8rem; letter-spacing: .1em; text-transform: uppercase; }
    .result-value { color: #a4ffdf; font-size: 2rem; font-weight: 750; margin-top: .2rem; }
    .fine-print { color: #91a29d; font-size: .84rem; line-height: 1.55; }
    div.stButton > button {
        border: 1px solid rgba(0, 255, 190, .55);
        border-radius: 12px;
        background: rgba(0, 255, 190, .09);
        color: #eafff8;
        box-shadow: 0 0 13px rgba(0, 255, 190, .09);
        transition: .18s ease;
    }
    div.stButton > button:hover {
        border-color: #53ffd0;
        background: rgba(0, 255, 190, .16);
        color: white;
        box-shadow: 0 0 22px rgba(0, 255, 190, .2);
    }
    div[data-testid="stColumn"]:has(.neon-card--red) div.stButton > button { border-color: #ff637b; background: rgba(255, 78, 105, .13); box-shadow: 0 0 17px rgba(255, 78, 105, .2); }
    div[data-testid="stColumn"]:has(.neon-card--blue) div.stButton > button { border-color: #55aeff; background: rgba(63, 165, 255, .13); box-shadow: 0 0 17px rgba(63, 165, 255, .2); }
    div[data-testid="stColumn"]:has(.neon-card--violet) div.stButton > button { border-color: #bd7dff; background: rgba(183, 109, 255, .13); box-shadow: 0 0 17px rgba(183, 109, 255, .2); }
    div[data-testid="stColumn"]:has(.neon-card--amber) div.stButton > button { border-color: #ffc65f; background: rgba(255, 184, 61, .13); box-shadow: 0 0 17px rgba(255, 184, 61, .2); }
    div[data-testid="stColumn"]:has(.neon-card--cyan) div.stButton > button { border-color: #4df4f4; background: rgba(45, 229, 230, .13); box-shadow: 0 0 17px rgba(45, 229, 230, .2); }
    div[data-testid="stColumn"]:has(.neon-card--pink) div.stButton > button { border-color: #ff76d6; background: rgba(255, 100, 207, .13); box-shadow: 0 0 17px rgba(255, 100, 207, .2); }
    div[data-testid="stColumn"]:has(.neon-card--orange) div.stButton > button { border-color: #ff9a45; background: rgba(255, 145, 54, .13); box-shadow: 0 0 17px rgba(255, 145, 54, .2); }
    div[data-testid="stColumn"]:has(.neon-card--lime) div.stButton > button { border-color: #c6ff5e; background: rgba(184, 255, 68, .13); box-shadow: 0 0 17px rgba(184, 255, 68, .2); }
    div[data-testid="stColumn"]:has(.neon-card--rainbow) div.stButton > button {
        border-color: #dc8aff;
        background: linear-gradient(110deg, rgba(255, 74, 120, .2), rgba(134, 83, 255, .2), rgba(0, 220, 210, .2));
        box-shadow: 0 0 20px rgba(255, 80, 150, .18), 0 0 26px rgba(65, 150, 255, .13);
    }
    div[data-testid="stForm"] {
        border: 1px solid rgba(115, 193, 255, .52);
        border-radius: 18px;
        padding: 1rem 1.2rem 1.15rem;
        background: linear-gradient(135deg, rgba(47, 134, 255, .075), rgba(179, 84, 255, .045) 52%, rgba(255, 120, 55, .045)), rgba(8, 14, 18, .62);
        box-shadow: 0 0 25px rgba(60, 150, 255, .10), 0 0 33px rgba(183, 109, 255, .07), inset 0 0 18px rgba(0, 220, 240, .025);
    }
    div[data-testid="stNumberInput"] input {
        border-color: rgba(101, 209, 255, .62);
        box-shadow: 0 0 10px rgba(64, 172, 255, .12);
    }
    div[data-testid="stNumberInput"] input:focus {
        border-color: #8bdcff;
        box-shadow: 0 0 15px rgba(64, 172, 255, .28);
    }
    div[data-testid="stSelectbox"] [data-baseweb="select"] > div {
        border-color: rgba(183, 109, 255, .65);
        box-shadow: 0 0 12px rgba(183, 109, 255, .14);
    }
    .personal-section {
        padding: .65rem .9rem;
        margin: 1.05rem 0 .45rem;
        border-radius: 12px;
        font-weight: 700;
        letter-spacing: .03em;
        background: rgba(10, 15, 20, .6);
    }
    .personal-section--orange { border: 1px solid rgba(255, 145, 54, .55); box-shadow: 0 0 15px rgba(255, 145, 54, .1); color: #ffc184; }
    .personal-section--blue { border: 1px solid rgba(63, 165, 255, .55); box-shadow: 0 0 15px rgba(63, 165, 255, .1); color: #83c8ff; }
    .personal-section--violet { border: 1px solid rgba(183, 109, 255, .55); box-shadow: 0 0 15px rgba(183, 109, 255, .1); color: #d3a6ff; }
    .personal-section--lime { border: 1px solid rgba(184, 255, 68, .52); box-shadow: 0 0 15px rgba(184, 255, 68, .1); color: #d3ff8c; }
    div[data-testid="stMetric"] {
        border: 1px solid rgba(185, 125, 255, .36);
        border-radius: 14px;
        padding: .8rem 1rem;
        background: linear-gradient(145deg, rgba(83, 102, 255, .07), rgba(255, 94, 175, .045)), rgba(12, 20, 22, .78);
        box-shadow: 0 0 15px rgba(132, 105, 255, .09);
    }
    div[data-testid="stVegaLiteChart"] {
        border: 1px solid rgba(107, 178, 255, .35);
        border-radius: 16px;
        padding: .45rem;
        background: linear-gradient(145deg, rgba(67, 117, 255, .055), rgba(255, 92, 176, .035)), rgba(9, 14, 18, .65);
        box-shadow: 0 0 17px rgba(82, 147, 255, .1);
    }
    </style>
    """,
    unsafe_allow_html=True,
)


def set_page(page: str) -> None:
    st.session_state.page = page


def render_choice_cards(
    heading: str,
    choices: tuple[tuple[str, str, str], ...],
    state_key: str,
    key_prefix: str,
) -> str:
    st.subheader(heading)
    columns = st.columns(3, gap="medium")
    current_choice = st.session_state[state_key]
    for index, (label, description, accent) in enumerate(choices):
        with columns[index % len(columns)]:
            selected_class = " choice-card--selected" if label == current_choice else ""
            st.markdown(
                f'<div class="neon-card choice-card neon-card--{accent}{selected_class}">'
                f'<div class="card-kicker">{"Selected" if label == current_choice else "Choose option"}</div>'
                f"<h3>{label}</h3><p>{description}</p></div>",
                unsafe_allow_html=True,
            )
            button_label = "Selected" if label == current_choice else f"Choose {label}"
            if st.button(
                button_label,
                key=f"{key_prefix}_{index}",
                width="stretch",
                type="primary" if label == current_choice else "secondary",
            ):
                st.session_state[state_key] = label
                st.session_state.page = "calculator"
                st.rerun()
    return current_choice


def render_contribution_chart(
    contributions: tuple[tuple[str, float], ...],
    key: str = "emissions_contribution_pie",
) -> None:
    positive_contributions = [
        (label, max(0.0, value)) for label, value in contributions if value > 0
    ]
    total = sum(value for _, value in positive_contributions)
    if total <= 0:
        st.info("Enter activity with non-zero emissions to see the input contribution chart.")
        return

    chart_data = pd.DataFrame(
        [
            {
                "Input": label,
                "Emissions (t CO2e)": value,
                "Share": value / total * 100,
                "Share label": f"{value / total * 100:.1f}%",
            }
            for label, value in positive_contributions
        ]
    )
    chart_spec = {
        "layer": [
            {
                "mark": {
                    "type": "arc",
                    "outerRadius": 112,
                    "stroke": "#070a0d",
                    "strokeWidth": 2,
                },
                "encoding": {
                    "theta": {
                        "field": "Emissions (t CO2e)",
                        "type": "quantitative",
                        "stack": True,
                    },
                    "color": {
                        "field": "Input",
                        "type": "nominal",
                        "scale": {"scheme": "rainbow"},
                        "legend": {"title": "Emissions source"},
                    },
                    "tooltip": [
                        {"field": "Input", "type": "nominal"},
                        {
                            "field": "Emissions (t CO2e)",
                            "type": "quantitative",
                            "format": ".3f",
                        },
                        {"field": "Share", "type": "quantitative", "format": ".1f"},
                    ],
                },
            },
            {
                "mark": {
                    "type": "text",
                    "radius": 138,
                    "fontSize": 12,
                    "fontWeight": "bold",
                    "color": "#ffffff",
                },
                "encoding": {
                    "theta": {
                        "field": "Emissions (t CO2e)",
                        "type": "quantitative",
                        "stack": True,
                    },
                    "text": {"field": "Share label", "type": "nominal"},
                },
            },
        ],
        "view": {"stroke": None},
    }
    st.subheader("Share of emissions by input")
    st.vega_lite_chart(chart_data, chart_spec, width="stretch", height=340, key=key)


def render_result(
    total_tonnes: float,
    intensity: float,
    benchmark: float | None,
    benchmark_label: str,
    suggestions: tuple[str, ...],
    contributions: tuple[tuple[str, float], ...],
) -> None:
    if benchmark is not None and benchmark <= 0:
        st.error("The reference intensity must be greater than zero to calculate a comparison.")
        return
    with st.container(border=True):
        st.subheader("Your estimate")
        metric_cols = st.columns(3 if benchmark is not None else 2)
        metric_cols[0].metric("Estimated emissions", f"{total_tonnes:,.2f} t CO2e / year")
        metric_cols[1].metric("Emissions intensity", f"{intensity:,.3f} {benchmark_label}")
        if benchmark is not None:
            difference = ((intensity / benchmark) - 1) * 100
            if difference > 0.05:
                comparison = f"{difference:.1f}% above reference"
            elif difference < -0.05:
                comparison = f"{abs(difference):.1f}% below reference"
            else:
                comparison = "At the reference level"
            metric_cols[2].metric("Comparison", comparison)

            st.markdown(
                f"""
                <div class="result-panel">
                  <div class="result-label">Reference intensity</div>
                  <div class="result-value">{benchmark:.3f} {benchmark_label}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            if difference > 0.05:
                st.warning(
                    f"This estimate is **{difference:.1f}% higher** than the reference intensity. "
                    "The reference is a comparison point, not a regulatory limit."
                )
            elif difference < -0.05:
                st.success(
                    f"This estimate is **{abs(difference):.1f}% below** the reference intensity. "
                    "Keep tracking actual production and energy data."
                )
            else:
                st.info("This estimate is at the reference intensity.")
        render_contribution_chart(contributions)
        st.markdown("**Practical ways to reduce emissions**")
        for suggestion in suggestions:
            st.markdown(f"- {suggestion}")


@st.dialog("A brighter way to understand emissions", width="large")
def welcome_dialog() -> None:
    st.markdown(
        "### Small calculations. Big-picture thinking."
        "\n\nExplore what carbon emissions mean, then estimate emissions for "
        "industry, crop farming, and ammonia production. No account or setup needed."
    )
    st.caption("Estimates are learning and screening tools; use verified local factors for reporting.")
    if st.button("Enter Carbon Compass", type="primary", width="stretch"):
        st.session_state.welcome_open = False
        st.rerun()


@st.dialog("Calculate CO2 emissions by category", width="large")
def category_dialog() -> None:
    st.write("Choose a sector to open its calculator.")
    left, middle, right = st.columns(3)
    options = [
        (
            left,
            "Industry-based emissions",
            "industry",
            "red",
            "Estimate factory energy and process emissions across five industries.",
        ),
        (
            middle,
            "Crop agriculture",
            "agriculture",
            "lime",
            "Estimate field fertilizer, farm diesel, and purchased-electricity emissions.",
        ),
        (
            right,
            "Ammonia plant emissions",
            "ammonia",
            "rainbow",
            "Combine hydrogen pathway emissions with electricity, onsite fuel, and other direct plant emissions.",
        ),
    ]
    for column, label, calculator, accent, description in options:
        with column:
            st.markdown(
                f'<div class="neon-card neon-card--{accent}">'
                f"<h3>{label}</h3><p>{description}</p></div>",
                unsafe_allow_html=True,
            )
            if st.button(label, key=f"choose_{calculator}", width="stretch"):
                st.session_state.page = "calculator_options"
                st.session_state.calculator = calculator
                st.session_state.category_dialog_open = False
                st.rerun()
    st.caption("Each calculator opens with its own inputs, formula, estimate, and reduction ideas.")


if "page" not in st.session_state:
    st.session_state.page = "home"
if "welcome_open" not in st.session_state:
    st.session_state.welcome_open = True
if "category_dialog_open" not in st.session_state:
    st.session_state.category_dialog_open = False
if "calculator" not in st.session_state:
    st.session_state.calculator = "industry"
if "industry_choice" not in st.session_state:
    st.session_state.industry_choice = next(iter(INDUSTRIES))
if st.session_state.get("agriculture_choice") not in {
    choice[0] for choice in CALCULATOR_CHOICES["agriculture"]
}:
    st.session_state.agriculture_choice = CALCULATOR_CHOICES["agriculture"][0][0]
legacy_route_map = {
    "Natural gas reforming": "Natural gas (grey hydrogen)",
    "Coal gasification": "Coal (high-carbon hydrogen)",
    "Renewable hydrogen": "Renewable electricity (green hydrogen)",
}
route = st.session_state.get("ammonia_route")
if route not in HYDROGEN_FACTORS:
    route = st.session_state.get("haber_route") or legacy_route_map.get(route)
st.session_state.ammonia_route = (
    route if route in HYDROGEN_FACTORS else next(iter(HYDROGEN_FACTORS))
)
if st.session_state.get("calculator") == "haber":
    st.session_state.calculator = "ammonia"

if st.session_state.welcome_open:
    welcome_dialog()
if st.session_state.category_dialog_open:
    category_dialog()

if st.session_state.page == "home":
    st.markdown(
        """
        <div class="hero">
          <div class="eyebrow">Understand. Measure. Improve.</div>
          <div class="hero-title">Carbon Compass</div>
          <div class="hero-copy">
            A clear, friendly starting point for understanding CO2 emissions
            and exploring practical ways to reduce them.
          </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.subheader("Choose your next step")
    learn_column, category_column, personal_column = st.columns(3, gap="medium")
    with learn_column:
        st.markdown(
            """
            <div class="neon-card neon-card--green">
              <div class="card-kicker">01 · Learn</div>
              <h3>Know about CO2 emissions</h3>
              <p>Discover what emissions are, why measurement matters, and how
              industry choices affect people, nature, and the climate.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Explore the impact", key="learn_button", width="stretch"):
            set_page("learn")
            st.rerun()
    with category_column:
        st.markdown(
            """
            <div class="neon-card neon-card--blue">
              <div class="card-kicker">02 · Calculate</div>
              <h3>Calculate emissions by category</h3>
                  <p>Estimate emissions from industry, crop agriculture, and ammonia plants
                  with sector-specific inputs, formulas, and reduction ideas.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button("Choose a calculator", key="calculate_button", type="primary", width="stretch"):
            st.session_state.category_dialog_open = True
            st.rerun()
    with personal_column:
        st.markdown(
            """
            <div class="neon-card neon-card--rainbow">
              <div class="card-kicker">03 · Your footprint</div>
              <h3>Personal carbon emissions</h3>
              <p>Estimate the yearly impact of your travel, home energy, flights,
              and food. Find your biggest area and practical ways to lower it.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if st.button(
            "Calculate my footprint",
            key="personal_calculate_button",
            width="stretch",
        ):
            set_page("personal")
            st.rerun()

    st.space("large")
    st.caption("A learning tool, not a verified greenhouse-gas inventory or compliance report.")

elif st.session_state.page == "learn":
    if st.button(":material/arrow_back: Back to home", key="learn_back"):
        set_page("home")
        st.rerun()
    st.markdown('<div class="eyebrow">The essentials</div>', unsafe_allow_html=True)
    st.title("Know about CO2 emissions")
    st.markdown(
        "Carbon dioxide (CO2) is part of the natural carbon cycle, but burning fossil fuels, "
        "making materials, and changing land use add carbon faster than natural systems can "
        "remove it. CO2 and other greenhouse gases trap heat in the atmosphere. Measuring "
        "emissions helps people see which activities contribute, compare options fairly, "
        "and decide where practical reductions can have the greatest effect."
    )

    topics = [
        (
            "Why calculate?",
            (
                "A footprint is an estimate of greenhouse gases associated with an activity, "
                "organization, or product. It turns a broad goal such as “use less energy” "
                "into questions that can be acted on: which fuel is used, where electricity "
                "is consumed, and how much is emitted for each tonne of product?",
                "Repeated measurements can uncover equipment running when idle, heat escaping "
                "from a process, or materials being wasted. They also help teams compare "
                "projects, set a baseline, and check whether a change really reduced emissions "
                "rather than shifting them elsewhere.",
            ),
        ),
        (
            "How industries contribute",
            (
                "Industrial emissions do not all come from the same place. Boilers, furnaces, "
                "and kilns release CO2 when they burn coal, oil, or gas. Purchased electricity "
                "can add indirect emissions depending on how the local grid makes power. Some "
                "chemical reactions release CO2 even before a factory uses any fuel.",
                "For example, limestone releases CO2 as it becomes clinker in cement-making. "
                "Hydrogen used in conventional ammonia production is often made from fossil "
                "fuel. A full product footprint can also include mining, farming, packaging, "
                "and transport beyond the factory gate.",
            ),
        ),
        (
            "What happens to environments?",
            (
                "As greenhouse gases build up, the Earth system retains more heat. This raises "
                "average temperatures and changes the odds of some extremes, including dangerous "
                "heat, heavy rainfall, drought, and coastal flooding. The effects differ by "
                "place and depend on many interacting natural and human factors.",
                "The ocean absorbs some of the extra CO2, which changes seawater chemistry and "
                "makes it harder for some organisms to build shells and skeletons. Ecosystems "
                "under stress can affect food, water, health, and livelihoods. Emissions "
                "measurement is one tool for understanding causes; it is not a forecast of "
                "the exact impact on a particular community.",
            ),
        ),
        (
            "CO2e and fair comparisons",
            (
                "Factories release gases besides CO2. Carbon dioxide equivalent (CO2e) "
                "expresses different greenhouse gases in a common unit using a chosen global "
                "warming potential and time horizon. The selected method matters: reported "
                "CO2e can differ if a standard uses different assessment values.",
                "Totals tell how much is emitted overall, while intensity divides emissions "
                "by useful output—for example, tonnes of CO2e per tonne of cement. Intensity "
                "helps compare production efficiency, but comparisons only make sense when "
                "the products, year, geography, lifecycle boundary, and gases counted are "
                "similar.",
            ),
        ),
        (
            "Three useful accounting scopes",
            (
                "Scope 1 covers direct emissions from sources an organization owns or controls, "
                "such as a site boiler or company vehicle. Scope 2 accounts for emissions from "
                "the electricity, steam, heating, or cooling the organization purchases. "
                "These categories help distinguish on-site fuel use from energy bought from "
                "a supplier.",
                "Scope 3 includes other upstream and downstream value-chain sources, such as "
                "purchased materials, outsourced freight, product use, and disposal. It can "
                "be the largest part of a footprint, but it is also harder to estimate. A "
                "useful inventory states which scopes are included and avoids counting the "
                "same emissions twice within its own boundary.",
            ),
        ),
        (
            "Small details with big connections",
            (
                "Ammonia is an important ingredient in fertilizers that help grow food. In "
                "many plants, making the hydrogen feedstock is the most energy-intensive step, "
                "so the source of that hydrogen strongly affects the footprint. A switch to "
                "renewable-powered hydrogen can lower emissions, but the result still depends "
                "on electricity, equipment, and supply-chain assumptions.",
                "Sugar mills can burn bagasse—the fibrous material left after juice extraction—"
                "to supply some of their heat and power. Cement has both fuel emissions and "
                "process emissions from limestone chemistry. These examples show why one "
                "generic “factory factor” cannot describe every industry accurately.",
            ),
        ),
    ]
    topic_colors = ["red", "blue", "violet", "amber", "cyan", "pink"]
    for start in range(0, len(topics), 2):
        columns = st.columns(2, gap="large")
        for column, (index, (title, paragraphs)) in zip(
            columns, enumerate(topics[start : start + 2], start=start)
        ):
            with column:
                body = "".join(f"<p>{paragraph}</p>" for paragraph in paragraphs)
                st.markdown(
                    f'<div class="neon-card topic-card neon-card--{topic_colors[index]}">'
                    f"<h3>{title}</h3>{body}</div>",
                    unsafe_allow_html=True,
                )
        st.space("medium")

    st.info(
        "The most useful comparison is usually emissions per unit of useful output, "
        "not just the total. A larger factory may emit more overall while producing "
        "each tonne more efficiently.",
        title="A fair comparison",
    )
    st.space("large")
    st.header("Emissions in context", icon=":material/monitoring:")
    st.write(
        "These charts use measured global atmospheric CO2 data and IPCC sector estimates. "
        "Atmospheric concentration is not the same thing as annual emissions: it is the "
        "amount of CO2 present in the air after emissions and natural uptake."
    )
    trend = pd.DataFrame(
        {
            "Year": GLOBAL_CO2_YEARS,
            "Global mean CO2 concentration (ppm)": GLOBAL_CO2_PPM,
        }
    )
    trend["Annual change in CO2 concentration (ppm)"] = (
        trend["Global mean CO2 concentration (ppm)"].diff()
    )
    chart_left, chart_right = st.columns(2, gap="large")
    with chart_left:
        st.subheader("CO2 in the atmosphere")
        st.line_chart(
            trend,
            x="Year",
            y="Global mean CO2 concentration (ppm)",
            x_label="Year",
            y_label="CO2 concentration (ppm)",
            alt="Global annual mean atmospheric CO2 concentration rose from 336.85 ppm in 1979 to 425.62 ppm in 2025",
        )
        st.caption(
            "NOAA Global Monitoring Laboratory annual global means, 1979–2025. "
            "[Open the dataset and methodology](https://gml.noaa.gov/ccgg/trends/gl_data.html)."
        )
    with chart_right:
        st.subheader("Year-to-year change")
        recent_changes = trend.loc[
            trend["Year"] >= 2006, ["Year", "Annual change in CO2 concentration (ppm)"]
        ].dropna()
        st.bar_chart(
            recent_changes,
            x="Year",
            y="Annual change in CO2 concentration (ppm)",
            x_label="Year",
            y_label="Change in annual mean (ppm)",
            alt="Year-to-year change in NOAA global annual mean atmospheric CO2 concentration from 2006 to 2025",
        )
        st.caption(
            "Each bar is the difference between adjacent annual means; the year-to-year "
            "change varies, but the long-term concentration trend rises."
        )

    st.subheader("Where global greenhouse gas emissions came from")
    st.bar_chart(
        IPCC_2019_SECTOR_SHARES,
        x="Sector",
        y="Share of global emissions (%)",
        x_label="Sector",
        y_label="Share of 2019 net anthropogenic GHG emissions (%)",
        horizontal=True,
        alt="In 2019, energy supply was the largest sector at 34 percent, followed by industry at 24 percent",
    )
    st.caption(
        "IPCC Sixth Assessment Report, Working Group III, 2019 net anthropogenic greenhouse "
        "gas emissions by sector. Shares sum to 101% due to rounding; AFOLU means agriculture, "
        "forestry and other land use. [Read the IPCC report](https://www.ipcc.ch/report/ar6/wg3/)."
    )
    st.space("large")
    st.header("Explore trusted resources", icon=":material/library_books:")
    resources = [
        (
            "NOAA Global Monitoring Laboratory",
            "Atmospheric CO2 measurements, annual data, methods, and change logs.",
            "https://gml.noaa.gov/ccgg/trends/gl_data.html",
        ),
        (
            "NASA: evidence for climate change",
            "A plain-language overview of observed changes in the climate system.",
            "https://science.nasa.gov/climate-change/evidence/",
        ),
        (
            "EPA: global warming potentials",
            "How CO2e compares different greenhouse gases and why time horizons matter.",
            "https://www.epa.gov/ghgemissions/understanding-global-warming-potentials",
        ),
        (
            "GHG Protocol corporate standards",
            "Guidance for organizational inventories, scopes, and consistent reporting.",
            "https://ghgprotocol.org/corporate-standard",
        ),
        (
            "IPCC AR6 Working Group III",
            "Evidence and pathways for reducing emissions across sectors.",
            "https://www.ipcc.ch/report/ar6/wg3/",
        ),
        (
            "IPCC agricultural emissions guidance",
            "Methods for estimating emissions from agriculture, forestry, and land use.",
            "https://www.ipcc-nggip.iges.or.jp/public/2019rf/vol4.html",
        ),
        (
            "IEA ammonia technology roadmap",
            "Technology options and emissions pathways for ammonia production.",
            "https://www.iea.org/reports/ammonia-technology-roadmap",
        ),
    ]
    resource_columns = st.columns(2, gap="large")
    for index, (title, description, url) in enumerate(resources):
        with resource_columns[index % 2]:
            st.markdown(f"**[{title}]({url})**  \n{description}")

elif st.session_state.page == "personal":
    if st.button(":material/arrow_back: Back to home", key="personal_back"):
        set_page("home")
        st.rerun()

    st.markdown('<div class="eyebrow">Your everyday impact</div>', unsafe_allow_html=True)
    st.title("Personal carbon emissions")
    st.write(
        "Estimate annual emissions using Indian household electricity and LPG inputs, "
        "Indian fuel-consumption units, and an India-specific per-person CO2 reference. "
        "Shared household energy is divided by the number of people in your home."
    )
    st.latex(
        r"\text{Personal annual CO2e} = \sum \left(\text{annual activity} \times \text{emissions factor}\right)"
    )
    st.caption(
        "This is a screening estimate, not a complete lifecycle inventory. The electricity "
        "factor is an India grid-average estimate; use your state or supplier factor if "
        "available. Transport and flight factors are indicative combustion/trip averages, "
        "not a vehicle- or route-specific Indian inventory."
    )

    with st.form("personal_form"):
        st.markdown(
            '<div class="personal-section personal-section--orange">Travel</div>',
            unsafe_allow_html=True,
        )
        petrol_litres = st.number_input(
            "Petrol used by your vehicles (litres per year)",
            min_value=0.0,
            value=300.0,
            step=25.0,
            key="personal_petrol_litres",
        )
        diesel_litres = st.number_input(
            "Diesel used by your vehicles (litres per year)",
            min_value=0.0,
            value=0.0,
            step=25.0,
            key="personal_diesel_litres",
        )
        cng_kg = st.number_input(
            "CNG used by your vehicles (kg per year)",
            min_value=0.0,
            value=0.0,
            step=10.0,
            key="personal_cng_kg",
        )
        transit_km = st.number_input(
            "Public bus or rail passenger distance (km per year)",
            min_value=0.0,
            value=2000.0,
            step=500.0,
            key="personal_transit_km",
        )

        st.markdown(
            '<div class="personal-section personal-section--blue">Home energy</div>',
            unsafe_allow_html=True,
        )
        household_members = st.number_input(
            "People sharing household energy",
            min_value=1,
            value=2,
            step=1,
            key="personal_household_members",
        )
        household_electricity = st.number_input(
            "Household electricity use (kWh per year)",
            min_value=0.0,
            value=3000.0,
            step=250.0,
            key="personal_electricity_kwh",
        )
        household_lpg_cylinders = st.number_input(
            "14.2 kg domestic LPG cylinders used (per year)",
            min_value=0.0,
            value=6.0,
            step=1.0,
            key="personal_lpg_cylinders",
        )

        st.markdown(
            '<div class="personal-section personal-section--violet">Air travel</div>',
            unsafe_allow_html=True,
        )
        domestic_flight_segments = st.number_input(
            "Domestic flight one-way segments (per year)",
            min_value=0,
            value=0,
            step=1,
            key="personal_domestic_flight_segments",
        )
        international_flight_segments = st.number_input(
            "International flight one-way segments (per year)",
            min_value=0,
            value=0,
            step=1,
            key="personal_international_flight_segments",
        )

        st.markdown(
            '<div class="personal-section personal-section--lime">Food</div>',
            unsafe_allow_html=True,
        )
        diet = st.selectbox(
            "Indicative food pattern (rough estimate)",
            list(DIET_FOOTPRINTS),
            key="personal_diet",
        )
        submitted = st.form_submit_button(
            "Estimate my annual footprint",
            type="primary",
            width="stretch",
        )

    if submitted:
        input_totals = {
            "Petrol": petrol_litres * PERSONAL_PETROL_KG_PER_LITRE / 1000,
            "Diesel": diesel_litres * PERSONAL_DIESEL_KG_PER_LITRE / 1000,
            "CNG": cng_kg * PERSONAL_CNG_KG_PER_KG / 1000,
            "Public transport": transit_km * PERSONAL_TRANSIT_KG_PER_KM / 1000,
            "Household electricity": (
                household_electricity * PERSONAL_GRID_KG_PER_KWH / 1000 / household_members
            ),
            "LPG": (
                household_lpg_cylinders * PERSONAL_LPG_TCO2_PER_CYLINDER / household_members
            ),
            "Domestic flights": (
                domestic_flight_segments * PERSONAL_DOMESTIC_FLIGHT_TONNES
            ),
            "International flights": (
                international_flight_segments * PERSONAL_INTERNATIONAL_FLIGHT_TONNES
            ),
        }
        food = DIET_FOOTPRINTS[diet]
        input_totals["Food pattern (estimate)"] = food
        category_totals = {
            "Travel": sum(
                input_totals[name]
                for name in ("Petrol", "Diesel", "CNG", "Public transport")
            ),
            "Home energy": input_totals["Household electricity"] + input_totals["LPG"],
            "Flights": input_totals["Domestic flights"] + input_totals["International flights"],
            "Food": food,
        }
        st.session_state.personal_result = {
            "total": sum(category_totals.values()),
            "categories": category_totals,
            "inputs": input_totals,
            "diet": diet,
        }

    if "personal_result" in st.session_state:
        result = st.session_state.personal_result
        category_totals = result["categories"]
        total = result["total"]
        largest_area = max(category_totals, key=category_totals.get)
        largest_value = category_totals[largest_area]
        largest_share = largest_value / total * 100 if total else 0
        difference = total - PERSONAL_REFERENCE_TCO2
        percent_difference = difference / PERSONAL_REFERENCE_TCO2 * 100

        st.space("large")
        st.header("Your results", icon=":material/analytics:")
        metric_columns = st.columns(3)
        metric_columns[0].metric("Estimated annual footprint", f"{total:.2f} t CO2e")
        metric_columns[1].metric(
            "Largest emissions area",
            largest_area,
            f"{largest_value:.2f} t CO2e · {largest_share:.0f}% of your estimate",
        )
        if difference >= 0:
            average_delta = f"{difference:.2f} t ({percent_difference:.1f}%) above"
        else:
            average_delta = f"{abs(difference):.2f} t ({abs(percent_difference):.1f}%) below"
        metric_columns[2].metric(
            "India per-person context",
            f"{PERSONAL_REFERENCE_TCO2:.2f} t CO2 / year",
            average_delta,
            delta_color="inverse",
        )

        if largest_value > 0:
            st.markdown(
                f"""
                <div class="neon-card neon-card--rainbow">
                  <div class="card-kicker">Your biggest opportunity</div>
                  <h3>{largest_area} is your largest estimated source</h3>
                  <p>It contributes <strong>{largest_value:.2f} tonnes CO2e per year</strong>,
                  or about <strong>{largest_share:.0f}%</strong> of the categories included here.</p>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.info("Your entered activities total zero. Add your annual activity to see your largest area.")

        chart_column, breakdown_column = st.columns(2, gap="large")
        with chart_column:
            render_contribution_chart(
                tuple(result.get("inputs", category_totals).items())
            )
        with breakdown_column:
            breakdown = pd.DataFrame(
                {
                    "Area": list(category_totals),
                    "Estimated annual emissions (t CO2e)": list(category_totals.values()),
                }
            ).sort_values("Estimated annual emissions (t CO2e)", ascending=False)
            st.bar_chart(
                breakdown,
                x="Area",
                y="Estimated annual emissions (t CO2e)",
                x_label="Personal emissions area",
                y_label="Estimated tonnes CO2e per year",
                horizontal=True,
                alt=f"Personal annual emissions by activity area, with {largest_area} the largest at {largest_value:.2f} tonnes CO2e",
            )

        reduction_ideas = {
            "Travel": (
                "Combine errands, avoid unnecessary car trips, and choose walking, cycling, car-sharing, or transit when practical.",
                "For your next vehicle, compare efficient or electric options using your local electricity mix.",
            ),
            "Home energy": (
                "Check for drafts, improve insulation where feasible, and lower heating or cooling waste.",
                "Choose efficient appliances and lighting; check whether your electricity supplier offers lower-carbon power.",
            ),
            "Flights": (
                "Replace a flight with rail or video meetings when practical, and combine trips where possible.",
                "If flying is necessary, fewer trips and direct routes can reduce travel-related emissions.",
            ),
            "Food": (
                "Try more plant-rich meals and reduce food waste through meal planning and storage.",
                "Choose seasonal foods and lower-impact proteins when they fit your diet and needs.",
            ),
        }
        st.subheader(f"Ways to reduce {largest_area.lower()} emissions")
        for idea in reduction_ideas[largest_area]:
            st.markdown(f"- {idea}")

        st.caption(
            f"Reference context: Our World in Data reports about {PERSONAL_REFERENCE_TCO2:.2f} tonnes "
            f"of territorial fossil CO2 per person in India in {PERSONAL_REFERENCE_YEAR}. "
            "This is a broad national context—not a like-for-like personal benchmark. It is "
            "territorial fossil CO2, while this estimate includes selected household, travel, "
            "flight, and illustrative food CO2e and omits many lifecycle and consumption emissions. "
            "[See India data and definitions](https://ourworldindata.org/grapher/co-emissions-per-capita?tab=chart&time=2025&country=~IND)."
        )
        st.caption(
            "India grid electricity uses an indicative 0.716 kg CO2/kWh default based on "
            "Central Electricity Authority grid-factor data; replace it with a current "
            "state- or supplier-specific factor where available. "
            "[Central Electricity Authority](https://cea.nic.in/). "
            "Other factors used: "
            "petrol 2.31 kg CO2/litre, diesel 2.68 kg/litre, CNG 2.75 kg/kg, LPG 0.0426 t "
            "CO2 per 14.2 kg cylinder; public transport 0.050 kg/passenger-km; domestic and "
            "international flight segments 0.15 t and 0.75 t respectively. Food-pattern values "
            "are rough illustrative estimates (1.0 / 1.5 / 2.2 t/person-year), not measured "
            "India-specific diet footprints. Use local, current factors for formal reporting."
        )

elif st.session_state.page == "calculator_options":
    if st.button(":material/arrow_back: Back to home", key="calculator_options_back"):
        set_page("home")
        st.rerun()

    calculator = st.session_state.calculator
    option_pages = {
        "industry": (
            "Choose an industry",
            "Select an industry to open its calculator on the next page.",
            "industry_choice",
            "industry_option",
        ),
        "agriculture": (
            "Choose an agriculture sector",
            "Select a farm sector to open its dedicated emissions calculator.",
            "agriculture_choice",
            "agriculture_option",
        ),
        "ammonia": (
            "Choose a hydrogen pathway",
            "Select the route used to supply hydrogen to the ammonia plant.",
            "ammonia_route",
            "ammonia_route_option",
        ),
    }
    heading, description, state_key, key_prefix = option_pages[calculator]
    st.markdown('<div class="eyebrow">Choose your process</div>', unsafe_allow_html=True)
    st.title(heading)
    st.write(description)
    render_choice_cards(
        heading,
        CALCULATOR_CHOICES[calculator],
        state_key,
        key_prefix,
    )

elif st.session_state.page == "calculator":
    back_column, home_column = st.columns(2)
    with back_column:
        if st.button(":material/arrow_back: Back to options", key="calculator_back"):
            set_page("calculator_options")
            st.rerun()
    with home_column:
        if st.button(":material/home: Back to home", key="calculator_home"):
            set_page("home")
            st.rerun()

    calculator = st.session_state.calculator
    if calculator == "industry":
        st.markdown('<div class="eyebrow">Sector calculator · 01</div>', unsafe_allow_html=True)
        st.title("Industry-based emissions")
        st.write(
            "Estimate operational emissions from electricity, fuel, and process sources. "
            f"Selected industry: **{st.session_state.industry_choice}**."
        )
        industry = st.session_state.industry_choice
        industry_data = INDUSTRIES[industry]
        st.latex(
            r"\text{Annual CO2e} = (\text{electricity MWh} \times \text{grid factor})"
            r" + (\text{fuel GJ} \times \text{fuel factor}) + \text{process CO2e}"
        )
        st.caption(
            "The calculator uses built-in screening factors: electricity 0.40 t CO2e/MWh "
            "and fuel 0.0561 t CO2e/GJ. Enter annual activity amounts; factors are kept "
            "out of the form to make it easier to use."
        )
        with st.form("industry_form"):
            production = st.number_input(
                industry_data["activity_label"],
                min_value=0.01,
                value=1000.0,
                step=100.0,
                key="industry_production",
            )
            electricity = st.number_input(
                "Purchased electricity (MWh per year)",
                min_value=0.0,
                value=500.0,
                step=50.0,
                key="industry_electricity",
            )
            fuel = st.number_input(
                industry_data["fuel_label"],
                min_value=0.0,
                value=5000.0,
                step=500.0,
                key="industry_fuel",
            )
            process = st.number_input(
                industry_data["process_label"],
                min_value=0.0,
                value=0.0,
                step=10.0,
                key="industry_process",
            )
            submitted = st.form_submit_button("Calculate industry emissions", type="primary")
        if submitted:
            electricity_emissions = electricity * GRID_TCO2_PER_MWH
            fuel_emissions = fuel * FUEL_TCO2_PER_GJ
            total = electricity_emissions + fuel_emissions + process
            intensity = total / production
            contributions = (
                ("Purchased electricity", electricity_emissions),
                ("Fuel", fuel_emissions),
                ("Process emissions", process),
            )
            st.session_state.industry_result = (
                total,
                intensity,
                industry,
                contributions,
                "fixed-factors-v1",
            )
        if "industry_result" in st.session_state:
            result = st.session_state.industry_result
            if (
                len(result) == 5
                and result[2] == industry
                and result[4] == "fixed-factors-v1"
            ):
                total, intensity, result_industry, contributions, _ = result
                render_result(
                    total,
                    intensity,
                    industry_data["reference"],
                    industry_data["reference_unit"],
                    industry_data["suggestions"],
                    contributions,
                )
            else:
                st.caption("Submit the form to refresh results and the input contribution chart.")
        st.caption(
            "Industry reference intensities are illustrative screening benchmarks, not official "
            "averages. They may not match your product mix, geography, or reporting boundary."
        )

    elif calculator == "agriculture":
        st.markdown('<div class="eyebrow">Sector calculator · 02</div>', unsafe_allow_html=True)
        sector = st.session_state.agriculture_choice
        st.title(f"{sector} emissions")
        sector_details = {
            "Crop farming": (
                "Estimate fertilizer-related soil N2O, farm electricity, and diesel use. "
                "Livestock, rice methane, land-use change, and fertilizer manufacturing are excluded.",
                r"\text{Annual CO2e} = \frac{\text{N kg} \times \text{soil factor kg CO2e/kg N}}{1000}"
                r" + (\text{electricity MWh} \times \text{grid factor t/MWh})"
                r" + \frac{\text{diesel litres} \times \text{diesel factor kg CO2e/litre}}{1000}",
            ),
            "Rice cultivation": (
                "Estimate methane from flooded rice fields alongside fertilizer, electricity, "
                "and diesel emissions. Enter annual hectare-seasons; the calculator uses a "
                "120-day flooded-season default.",
                r"\text{Annual CO2e} = \text{area ha-season} \times "
                r"\text{fixed rice methane factor t CO2e/ha-season}"
                r" + \text{fertilizer, electricity, and diesel CO2e}",
            ),
            "Dairy & cattle": (
                "Estimate herd methane from enteric fermentation and manure, plus farm electricity. "
                "Results vary substantially by animal, feed, and manure management.",
                r"\text{Annual CO2e} = \frac{\text{cattle} \times "
                r"(\text{enteric CH4 + manure CH4 kg/head/year}) \times \text{GWP}}{1000}"
                r" + \text{farm electricity CO2e}",
            ),
            "Poultry farming": (
                "Estimate poultry farm energy use. Manure emissions are excluded because they "
                "require flock and manure-management details.",
                r"\text{Annual CO2e} = "
                r"(\text{electricity MWh} \times \text{grid factor}) + \text{diesel CO2e}",
            ),
        }
        description, formula = sector_details[sector]
        st.write(description)
        st.latex(formula)
        if sector == "Crop farming":
            st.caption(
                "Built-in screening defaults: soil N2O 4.3 kg CO2e/kg nitrogen, electricity "
                f"{GRID_TCO2_PER_MWH:.2f} t CO2e/MWh, diesel "
                f"{AGRICULTURE_DIESEL_KG_PER_LITRE:.2f} kg CO2e/litre."
            )
        elif sector == "Rice cultivation":
            st.caption(
                f"Built-in screening defaults: methane {RICE_METHANE_KG_PER_HA_DAY:.2f} "
                f"kg/ha/day for {RICE_FLOODED_DAYS_PER_SEASON} days, methane GWP100 "
                f"{AGRICULTURE_METHANE_GWP100:.1f}, soil N2O 4.3 kg CO2e/kg nitrogen, "
                f"electricity {GRID_TCO2_PER_MWH:.2f} t CO2e/MWh, diesel "
                f"{AGRICULTURE_DIESEL_KG_PER_LITRE:.2f} kg CO2e/litre."
            )
        elif sector == "Dairy & cattle":
            st.caption(
                "Uses illustrative default factors of 60 kg enteric methane and 5 kg manure "
                f"methane per animal-year, methane GWP100 {AGRICULTURE_METHANE_GWP100:.1f}, "
                f"and electricity {GRID_TCO2_PER_MWH:.2f} t CO2e/MWh."
            )
        else:
            st.caption(
                f"Built-in energy defaults: electricity {GRID_TCO2_PER_MWH:.2f} t CO2e/MWh "
                f"and diesel {AGRICULTURE_DIESEL_KG_PER_LITRE:.2f} kg CO2e/litre. "
                "Manure emissions are excluded."
            )
        with st.form("agriculture_form"):
            if sector == "Crop farming":
                production = st.number_input(
                    "Crop output (tonnes per year)",
                    min_value=0.01,
                    value=1000.0,
                    step=100.0,
                    key="agriculture_production",
                )
                nitrogen = st.number_input(
                    "Nitrogen fertilizer applied (kg of nitrogen per year)",
                    min_value=0.0,
                    value=5000.0,
                    step=250.0,
                    key="agriculture_nitrogen",
                )
                electricity = st.number_input(
                    "Farm electricity (MWh per year)",
                    min_value=0.0,
                    value=100.0,
                    step=10.0,
                    key="agriculture_electricity",
                )
                diesel = st.number_input(
                    "Farm diesel use (litres per year)",
                    min_value=0.0,
                    value=1000.0,
                    step=100.0,
                    key="agriculture_diesel",
                )
                production_unit = "t crop"
            elif sector == "Rice cultivation":
                production = st.number_input(
                    "Rice output (tonnes per year)",
                    min_value=0.01,
                    value=1000.0,
                    step=100.0,
                    key="rice_production",
                )
                area = st.number_input(
                    "Rice area (hectare-seasons per year)",
                    min_value=0.0,
                    value=500.0,
                    step=25.0,
                    key="rice_area",
                )
                nitrogen = st.number_input(
                    "Nitrogen fertilizer applied (kg of nitrogen per year)",
                    min_value=0.0,
                    value=5000.0,
                    step=250.0,
                    key="rice_nitrogen",
                )
                electricity = st.number_input(
                    "Farm electricity (MWh per year)",
                    min_value=0.0,
                    value=100.0,
                    step=10.0,
                    key="rice_electricity",
                )
                diesel = st.number_input(
                    "Farm diesel use (litres per year)",
                    min_value=0.0,
                    value=1000.0,
                    step=100.0,
                    key="rice_diesel",
                )
                production_unit = "t rice"
            elif sector == "Dairy & cattle":
                production = st.number_input(
                    "Milk or livestock product output (tonnes per year)",
                    min_value=0.01,
                    value=500.0,
                    step=50.0,
                    key="cattle_production",
                )
                herd = st.number_input(
                    "Average cattle herd size (animals)",
                    min_value=0,
                    value=100,
                    step=10,
                    key="cattle_herd",
                )
                electricity = st.number_input(
                    "Farm electricity (MWh per year)",
                    min_value=0.0,
                    value=100.0,
                    step=10.0,
                    key="cattle_electricity",
                )
                production_unit = "t product"
            else:
                production = st.number_input(
                    "Poultry meat or egg output (tonnes per year)",
                    min_value=0.01,
                    value=500.0,
                    step=50.0,
                    key="poultry_production",
                )
                electricity = st.number_input(
                    "Farm electricity (MWh per year)",
                    min_value=0.0,
                    value=100.0,
                    step=10.0,
                    key="poultry_electricity",
                )
                diesel = st.number_input(
                    "Farm diesel use (litres per year)",
                    min_value=0.0,
                    value=1000.0,
                    step=100.0,
                    key="poultry_diesel",
                )
                production_unit = "t poultry product"
            submitted = st.form_submit_button(
                f"Calculate {sector.lower()} emissions",
                type="primary",
            )
        if submitted:
            if sector == "Crop farming":
                contributions = (
                    (
                        "Nitrogen fertilizer (direct soil N2O)",
                        nitrogen * AGRICULTURE_SOIL_KG_PER_KG_N / 1000,
                    ),
                    ("Farm electricity", electricity * GRID_TCO2_PER_MWH),
                    (
                        "Farm diesel",
                        diesel * AGRICULTURE_DIESEL_KG_PER_LITRE / 1000,
                    ),
                )
            elif sector == "Rice cultivation":
                contributions = (
                    (
                        "Rice-field methane",
                        area
                        * RICE_FLOODED_DAYS_PER_SEASON
                        * RICE_METHANE_KG_PER_HA_DAY
                        * AGRICULTURE_METHANE_GWP100
                        / 1000,
                    ),
                    (
                        "Nitrogen fertilizer (direct soil N2O)",
                        nitrogen * AGRICULTURE_SOIL_KG_PER_KG_N / 1000,
                    ),
                    ("Farm electricity", electricity * GRID_TCO2_PER_MWH),
                    (
                        "Farm diesel",
                        diesel * AGRICULTURE_DIESEL_KG_PER_LITRE / 1000,
                    ),
                )
            elif sector == "Dairy & cattle":
                contributions = (
                    (
                        "Enteric fermentation methane",
                        herd
                        * CATTLE_ENTERIC_METHANE_KG_PER_HEAD_YEAR
                        * AGRICULTURE_METHANE_GWP100
                        / 1000,
                    ),
                    (
                        "Manure methane",
                        herd
                        * CATTLE_MANURE_METHANE_KG_PER_HEAD_YEAR
                        * AGRICULTURE_METHANE_GWP100
                        / 1000,
                    ),
                    ("Farm electricity", electricity * GRID_TCO2_PER_MWH),
                )
            else:
                contributions = (
                    ("Farm electricity", electricity * GRID_TCO2_PER_MWH),
                    (
                        "Farm diesel",
                        diesel * AGRICULTURE_DIESEL_KG_PER_LITRE / 1000,
                    ),
                )
            total = sum(value for _, value in contributions)
            intensity = total / production
            st.session_state.agriculture_result = (
                total,
                intensity,
                sector,
                production_unit,
                contributions,
                "fixed-factors-v1",
            )
        if "agriculture_result" in st.session_state:
            result = st.session_state.agriculture_result
            if (
                len(result) == 6
                and result[2] == sector
                and result[5] == "fixed-factors-v1"
            ):
                total, intensity, _, result_unit, contributions, _ = result
                if sector == "Crop farming":
                    suggestions = (
                        "Use soil testing and crop-specific nutrient plans to apply only the nitrogen needed.",
                        "Improve irrigation and pump efficiency, and use renewable electricity where feasible.",
                        "Reduce field passes, maintain farm equipment, and consider lower-carbon fuels.",
                    )
                elif sector == "Rice cultivation":
                    suggestions = (
                        "Use alternate wetting and drying where suitable to reduce methane from continuously flooded fields.",
                        "Match nitrogen timing and amount to crop needs and avoid unnecessary fertilizer application.",
                        "Improve pump efficiency and reduce diesel use for irrigation and field operations.",
                    )
                elif sector == "Dairy & cattle":
                    suggestions = (
                        "Improve animal health, feed quality, and productivity to reduce emissions per unit of milk or product.",
                        "Capture or treat manure methane where practical, and manage manure to limit anaerobic storage.",
                        "Use efficient equipment and lower-carbon electricity for milking, cooling, and water pumping.",
                    )
                else:
                    suggestions = (
                        "Keep litter dry, manage ventilation carefully, and avoid excess manure accumulation.",
                        "Improve feed conversion, animal health, and housing efficiency to lower emissions per tonne of product.",
                        "Use efficient ventilation, heating, and lighting equipment and reduce farm energy waste.",
                    )
                render_result(
                    total,
                    intensity,
                    None,
                    f"t CO2e / {result_unit}",
                    suggestions,
                    contributions,
                )
            else:
                st.caption("Submit the form to refresh results and the input contribution chart.")
        st.caption(
            "Agriculture factors vary by crop, animal, climate, water and manure management, "
            "and reporting boundary; use locally applicable factors where possible. Technical "
            "emissions factors are built in rather than entered as form inputs. The crop soil "
            "factor is a simplified direct N2O estimate, rice and cattle factors are screening "
            "defaults, and poultry manure emissions are excluded. The IPCC guidance provides "
            "methods but not one universal farm-sector average: "
            "[IPCC 2019 Refinement, AFOLU](https://www.ipcc-nggip.iges.or.jp/public/2019rf/vol4.html)."
        )

    else:
        st.markdown('<div class="eyebrow">Sector calculator · 03</div>', unsafe_allow_html=True)
        st.title("Ammonia plant emissions")
        route = st.session_state.ammonia_route
        st.write(
            "The Haber-Bosch process is the ammonia-synthesis step, not a separate plant "
            "footprint. This screening estimate combines the selected hydrogen pathway "
            f"with purchased electricity. Selected pathway: **{route}**."
        )
        st.latex(
            r"\text{Annual CO2e} = "
            r"\frac{\text{NH3 tonnes} \times 180\text{ kg H2/t} \times "
            r"\text{pathway factor kg CO2e/kg H2}}{1000}"
            r" + \text{electricity MWh} \times 0.40\text{ t CO2e/MWh}"
        )
        st.caption(
            f"The selected pathway starts with an illustrative factor of {HYDROGEN_FACTORS[route]:.1f} "
            "kg CO2e/kg H2. Hydrogen use is assumed to be 180 kg per tonne ammonia and the "
            "grid factor 0.40 t CO2e/MWh. Onsite fuel and other direct process emissions are "
            "not included; use a detailed plant inventory for full reporting."
        )
        with st.form("ammonia_form"):
            production = st.number_input(
                "Ammonia production (tonnes per year)",
                min_value=0.01,
                value=1000.0,
                step=100.0,
                key="ammonia_production",
            )
            electricity = st.number_input(
                "Purchased electricity (MWh per year)",
                min_value=0.0,
                value=900.0,
                step=100.0,
                key="ammonia_electricity",
            )
            submitted = st.form_submit_button("Calculate ammonia plant emissions", type="primary")
        if submitted:
            pathway_emissions = production * 180 * HYDROGEN_FACTORS[route] / 1000
            electricity_emissions = electricity * GRID_TCO2_PER_MWH
            total = pathway_emissions + electricity_emissions
            intensity = total / production
            contributions = (
                ("Hydrogen pathway", pathway_emissions),
                ("Purchased electricity", electricity_emissions),
            )
            st.session_state.ammonia_result = (
                total,
                intensity,
                route,
                contributions,
                "simple-boundary-v1",
            )
        if "ammonia_result" in st.session_state:
            result = st.session_state.ammonia_result
            if len(result) == 5 and result[2] == route and result[4] == "simple-boundary-v1":
                total, intensity, result_route, contributions, _ = result
                render_result(
                    total,
                    intensity,
                    2.4,
                    "t CO2e / t ammonia",
                    (
                        "Switch to renewable-powered hydrogen where its lifecycle factor is demonstrably lower.",
                        "Improve heat integration and replace onsite fossil fuel with low-carbon heat.",
                        "Reduce electricity use and procure lower-carbon power; verify supplier-specific factors.",
                    ),
                    contributions,
                )
            else:
                st.caption("Submit the form to refresh results and the input contribution chart.")
        st.caption(
            "The 2.4 t CO2e/t ammonia reference is an indicative screening benchmark, not an official average. "
            "The selected hydrogen factor includes its pathway emissions; do not enter those same emissions "
            "again in another calculator. This quick estimate excludes onsite fuel and other direct "
            "process emissions. Use plant-specific lifecycle and location-based data for full reporting."
        )

st.markdown(
    '<p class="fine-print">Carbon Compass · Estimates are only as reliable as their inputs and factors. '
    "Check local, current, independently verified emissions factors before using results for decisions or reporting.</p>",
    unsafe_allow_html=True,
)
