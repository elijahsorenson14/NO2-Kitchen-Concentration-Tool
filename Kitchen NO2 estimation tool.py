import math
import ipywidgets as widgets
from IPython.display import display, clear_output

# -------------------------------------------------
# Governing model
# -------------------------------------------------

def predict_no2_concentration(E, eta, V, lambd_hr, t, C0=0):

    lambd = lambd_hr / 60
    A = E * (1 - eta) / V

    if abs(lambd) < 1e-10:
        return C0 + A * t
    else:
        return C0 * math.exp(-lambd * t) + (A / lambd) * (1 - math.exp(-lambd * t))


# -------------------------------------------------
# Realistic residential scenario mappings
# -------------------------------------------------

# Burner emission rate mapping (mg/min)
emission_options = {
    "Low burner usage (E = 0.5 mg/min)": 0.5,
    "Normal single burner cooking (E = 1 mg/min)": 1,
    "Multiple burners / moderate cooking (E = 2.5 mg/min)": 2.5,
    "High flame cooking (E = 3 mg/min)": 3,
    "Custom value...": None
}

# Hood capture efficiency mapping (0–0.8 is reasonable residential range)
hood_options = {
    "Hood off (η = 0.0)": 0.0,
    "Inefficient hood (η = 0.2)": 0.2,
    "Average hood (η = 0.4)": 0.4,
    "Efficient hood (η = 0.6)": 0.6,
    "Highly efficient hood (η = 0.8)": 0.8,
    "Custom value...": None
}

# Air exchange rate mapping (hr⁻¹)
ventilation_options = {
    "Windows closed (λ = 0.5 hr⁻¹)": 0.5,
    "Cracked window (λ = 1 hr⁻¹)": 1,
    "Partially open window (λ = 2 hr⁻¹)": 2,
    "Fully open ventilation (λ = 4 hr⁻¹)": 4,
    "Custom value...": None
}


# -------------------------------------------------
# Hybrid selector builder
# -------------------------------------------------

def build_hybrid_input(options_dict, label):

    dropdown = widgets.Dropdown(
        options=list(options_dict.keys()),
        value=list(options_dict.keys())[0],
        description=label,
        style={'description_width': 'initial'}
    )

    custom_input = widgets.FloatText(
        description="Custom value:",
        style={'description_width': 'initial'},
        layout=widgets.Layout(display='none')
    )

    def toggle_custom(change):
        if change['new'] == "Custom value...":
            custom_input.layout.display = 'block'
        else:
            custom_input.layout.display = 'none'

    dropdown.observe(toggle_custom, names='value')

    return dropdown, custom_input


# -------------------------------------------------
# Build controls
# -------------------------------------------------

E_dropdown, E_custom = build_hybrid_input(emission_options, "Burner behavior (E):")

V_widget = widgets.FloatText(
    value=40,
    description="Kitchen volume (V) m³:",
    style={'description_width': 'initial'}
)

t_widget = widgets.FloatText(
    value=30,
    description="Cooking duration (t) min:",
    style={'description_width': 'initial'}
)

C0_widget = widgets.FloatText(
    value=0,
    description="Initial concentration (C₀) mg/m³:",
    style={'description_width': 'initial'}
)

# Scenario 1
eta_dropdown, eta_custom = build_hybrid_input(hood_options, "Scenario 1 hood (η₁):")
lambda_dropdown, lambda_custom = build_hybrid_input(ventilation_options, "Scenario 1 ventilation (λ₁):")

# Scenario 2
eta2_dropdown, eta2_custom = build_hybrid_input(hood_options, "Scenario 2 hood (η₂):")
lambda2_dropdown, lambda2_custom = build_hybrid_input(ventilation_options, "Scenario 2 ventilation (λ₂):")

# Scenario 3
eta3_dropdown, eta3_custom = build_hybrid_input(hood_options, "Scenario 3 hood (η₃):")
lambda3_dropdown, lambda3_custom = build_hybrid_input(ventilation_options, "Scenario 3 ventilation (λ₃):")

for w in [eta2_dropdown, lambda2_dropdown, eta3_dropdown, lambda3_dropdown]:
    w.layout.display = 'none'


# -------------------------------------------------
# Comparison checkboxes
# -------------------------------------------------

compare2_widget = widgets.Checkbox(
    value=False,
    description="Enable Scenario 2 comparison"
)

compare3_widget = widgets.Checkbox(
    value=False,
    description="Enable Scenario 3 comparison"
)


# -------------------------------------------------
# Helper extraction
# -------------------------------------------------

def get_value(dropdown, custom_box, mapping):

    if dropdown.value == "Custom value...":
        return custom_box.value
    return mapping[dropdown.value]


# -------------------------------------------------
# Tool execution
# -------------------------------------------------

output = widgets.Output()

def run_tool(button):

    with output:
        clear_output()

        E = get_value(E_dropdown, E_custom, emission_options)

        V = V_widget.value
        t = t_widget.value
        C0 = C0_widget.value

        # Scenario 1
        eta1 = get_value(eta_dropdown, eta_custom, hood_options)
        lambd_hr_1 = get_value(lambda_dropdown, lambda_custom, ventilation_options)

        C1 = predict_no2_concentration(E, eta1, V, lambd_hr_1, t, C0)

        EPA_LIMIT = 0.188

        print("=== NO₂ Exposure Estimation Tool Output ===")
        print(f"NO₂ concentration after {t:.0f} minutes: {C1:.4f} mg/m³")

        print("\n--- Health Benchmark Comparison ---")
        print(f"EPA 1-hour guideline ≈ {EPA_LIMIT} mg/m³")

        if C1 > EPA_LIMIT:
            print("Warning: Predicted concentration exceeds the 1-hour guideline.")
        else:
            print("Predicted concentration is below the guideline.")

        results = [("Scenario 1", C1)]

        # Scenario 2
        if compare2_widget.value:

            eta2 = get_value(eta2_dropdown, eta2_custom, hood_options)
            lambd_hr_2 = get_value(lambda2_dropdown, lambda2_custom, ventilation_options)

            C2 = predict_no2_concentration(E, eta2, V, lambd_hr_2, t, C0)
            results.append(("Scenario 2", C2))

        # Scenario 3
        if compare3_widget.value:

            eta3 = get_value(eta3_dropdown, eta3_custom, hood_options)
            lambd_hr_3 = get_value(lambda3_dropdown, lambda3_custom, ventilation_options)

            C3 = predict_no2_concentration(E, eta3, V, lambd_hr_3, t, C0)
            results.append(("Scenario 3", C3))

        if len(results) > 1:

            print("\n--- Scenario Comparison ---")

            for label, value in results:
                print(f"{label} C(t) = {value:.4f} mg/m³")

            best = min(results, key=lambda x: x[1])
            print(f"\nResult: {best[0]} has the lowest predicted concentration.")


# -------------------------------------------------
# Dynamic UI behavior
# -------------------------------------------------

def toggle_comparison(change):

    widget_groups = {
        compare2_widget: [eta2_dropdown, lambda2_dropdown],
        compare3_widget: [eta3_dropdown, lambda3_dropdown]
    }

    for checkbox, controls in widget_groups.items():

        if checkbox.value:
            for w in controls:
                w.layout.display = 'block'
        else:
            for w in controls:
                w.layout.display = 'none'


compare2_widget.observe(toggle_comparison, names='value')
compare3_widget.observe(toggle_comparison, names='value')


# -------------------------------------------------
# Display UI
# -------------------------------------------------

button = widgets.Button(description="Run Exposure Tool")
button.on_click(run_tool)

display(
    E_dropdown,
    E_custom,

    V_widget,
    t_widget,
    C0_widget,

    eta_dropdown,
    eta_custom,

    lambda_dropdown,
    lambda_custom,

    compare2_widget,
    eta2_dropdown,
    lambda2_dropdown,

    compare3_widget,
    eta3_dropdown,
    lambda3_dropdown,

    button,
    output
)



