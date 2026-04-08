import streamlit as st
from streamlit_lottie import st_lottie
import machine_learning as ml
import feature_extraction as fe
from bs4 import BeautifulSoup
import requests
from PIL import Image
from textwrap import dedent

FEATURE_COLUMNS = [
    "has_title", "has_input", "has_button", "has_image", "has_submit",
    "has_link", "has_password", "has_email_input", "has_hidden_element",
    "has_audio", "has_video", "number_of_inputs", "number_of_buttons",
    "number_of_images", "number_of_option", "number_of_list", "number_of_th",
    "number_of_tr", "number_of_href", "number_of_paragraph", "number_of_script",
    "length_of_title", "has_h1", "has_h2", "has_h3", "length_of_text",
    "number_of_clickable_button", "number_of_a", "number_of_img", "number_of_div",
    "number_of_figure", "has_footer", "has_form", "has_text_area", "has_iframe",
    "has_text_input", "number_of_meta", "has_nav", "has_object", "has_picture",
    "number_of_sources", "number_of_span", "number_of_table",
]


def _vector_for_model(model, soup):
    import pandas as pd

    raw_vector = fe.create_vector(soup)
    values_by_name = dict(zip(FEATURE_COLUMNS, raw_vector))

    if hasattr(model, "feature_names_in_"):
        ordered = {name: [values_by_name.get(name, 0)] for name in model.feature_names_in_}
        return pd.DataFrame(ordered)

    expected = getattr(model, "n_features_in_", None)
    if isinstance(expected, int):
        if len(raw_vector) < expected:
            raw_vector = raw_vector + [0] * (expected - len(raw_vector))
        return pd.DataFrame([raw_vector[:expected]], columns=FEATURE_COLUMNS[:expected])

    return pd.DataFrame([raw_vector], columns=FEATURE_COLUMNS[: len(raw_vector)])


def _render_html(html: str):
    st.markdown(dedent(html).strip(), unsafe_allow_html=True)


def _inject_ml_styles():
    st.markdown(
        """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=DM+Sans:wght@300;400;500&display=swap');

    :root {
        --navy: #05112a;
        --navy2: #0a1f45;
        --teal: #00c9b1;
        --teal2: #00e5cc;
        --white: #f0f6ff;
        --gray: #8899bb;
        --border: rgba(0,201,177,0.2);
        --card: rgba(10,31,69,0.6);
    }

    .section-badge {
        display: inline-flex; align-items: center; gap: 8px;
        background: rgba(0,201,177,0.08);
        border: 1px solid var(--border);
        border-radius: 50px; padding: 5px 14px;
        font-size: 11px; color: var(--teal);
        font-weight: 700; letter-spacing: 1.5px;
        text-transform: uppercase; margin-bottom: 14px;
    }
    .section-title {
        font-family: 'Syne', sans-serif;
        font-size: clamp(28px, 4vw, 44px);
        font-weight: 800; color: var(--white);
        line-height: 1.15; margin-bottom: 10px;
    }
    .section-title span { color: var(--teal); }
    .section-sub { color: var(--gray); font-size: 15px; line-height: 1.7; max-width: 560px; font-weight: 300; }

    .ml-hero {
        background: linear-gradient(135deg, #061830 0%, #0a1f45 100%);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 52px 56px;
        margin-bottom: 32px;
        position: relative; overflow: hidden;
    }
    .ml-hero-glow {
        position:absolute; width:350px; height:350px;
        border-radius:50%; filter:blur(90px);
        background:rgba(0,201,177,0.07);
        top:-80px; right:-60px;
    }

    .stats-row { display: flex; gap: 16px; margin: 28px 0; flex-wrap: wrap; }
    .stat-card {
        flex: 1; min-width: 140px;
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px; padding: 20px 24px;
        text-align: center;
    }
    .stat-num { font-family: 'Syne', sans-serif; font-size: 28px; font-weight: 800; color: var(--teal); }
    .stat-label { font-size: 12px; color: var(--gray); margin-top: 4px; }

    .detect-card {
        background: linear-gradient(135deg, #061830 0%, #0c1e3d 100%);
        border: 1px solid var(--border);
        border-radius: 20px;
        padding: 44px 48px;
        margin: 32px 0;
    }

    .result-modal {
        position: relative;
        border-radius: 24px;
        padding: 44px 48px;
        margin-top: 28px;
        overflow: hidden;
    }
    .modal-safe {
        background: linear-gradient(135deg, #021a10 0%, #031f14 100%);
        border: 1px solid rgba(0,230,118,0.25);
    }
    .modal-phish {
        background: linear-gradient(135deg, #1a0208 0%, #1f030c 100%);
        border: 1px solid rgba(255,77,109,0.25);
    }

    .modal-icon {
        width: 72px; height: 72px; border-radius: 20px;
        display: flex; align-items: center; justify-content: center;
        font-size: 32px; margin-bottom: 20px;
    }
    .icon-safe  { background: rgba(0,230,118,0.12); border: 1px solid rgba(0,230,118,0.25); }
    .icon-phish { background: rgba(255,77,109,0.12); border: 1px solid rgba(255,77,109,0.25); }

    .modal-title {
        font-family: 'Syne', sans-serif;
        font-size: 30px; font-weight: 800;
        line-height: 1.1; margin-bottom: 10px;
    }
    .modal-title-safe  { color: #00e676; }
    .modal-title-phish { color: #ff4d6d; }
    .modal-desc { color: #8899bb; font-size: 15px; line-height: 1.7; margin-bottom: 28px; }

    .redirect-note {
        display:inline-flex; align-items:center; gap:8px;
        background: rgba(255,193,7,0.08); border:1px solid rgba(255,193,7,0.2);
        border-radius:8px; padding:8px 14px;
        font-size:12px; color:#ffc107; margin-bottom:16px;
    }

    .result-warn {
        background: linear-gradient(135deg,#1a1400 0%,#1f1800 100%);
        border:1px solid rgba(255,193,7,0.25);
        border-radius:20px; padding:32px 36px; margin-top:20px;
    }
    .result-warn-title {
        font-family:'Syne',sans-serif; font-size:22px; font-weight:800;
        color:#ffc107; margin-bottom:8px;
    }

    .dataset-card {
        background: var(--card);
        border: 1px solid var(--border);
        border-radius: 14px; padding: 28px 32px;
        margin: 16px 0;
    }
    .dataset-title {
        font-family: 'Syne', sans-serif;
        font-size: 16px; font-weight: 700;
        color: var(--white); margin-bottom: 8px;
    }

    .stSelectbox > div > div,
    .stTextInput input {
        background: rgba(255,255,255,0.04) !important;
        border: 1px solid rgba(255,255,255,0.1) !important;
        border-radius: 10px !important;
        color: var(--white) !important;
    }
    .stSelectbox label, .stTextInput label {
        color: var(--gray) !important;
        font-size: 12px !important;
        letter-spacing: 0.8px;
        text-transform: uppercase;
    }

    div[data-testid="stButton"] button {
        background: var(--teal) !important;
        color: var(--navy) !important;
        font-family: 'Syne', sans-serif !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        border: none !important;
        font-size: 15px !important;
    }

    .ml-divider { height: 1px; background: var(--border); margin: 36px 0; }
    </style>
    """,
        unsafe_allow_html=True,
    )


def ml_app():
    _inject_ml_styles()

    def load_lottieurl(url):
        try:
            r = requests.get(url, timeout=5)
            return r.json() if r.status_code == 200 else None
        except Exception:
            return None

    left, right = st.columns([2, 1])
    with left:
        _render_html(
            """
        <div class="ml-hero">
            <div class="ml-hero-glow"></div>
            <div style="position:relative;z-index:1;">
                <div class="section-badge">Phishing Detection Engine</div>
                <div class="section-title">Welcome,<br><span>Knight.</span></div>
                <p class="section-sub">
                    A content-based Machine Learning app that detects phishing websites
                    using advanced HTML feature extraction and 7 trained ML classifiers.
                </p>
                <div class="stats-row">
                    <div class="stat-card"><div class="stat-num">31,600</div><div class="stat-label">Websites Analysed</div></div>
                    <div class="stat-card"><div class="stat-num">7</div><div class="stat-label">ML Models</div></div>
                    <div class="stat-card"><div class="stat-num">43</div><div class="stat-label">HTML Features</div></div>
                    <div class="stat-card"><div class="stat-num">97%+</div><div class="stat-label">Top Accuracy</div></div>
                </div>
            </div>
        </div>
        """
        )

    with right:
        lottie_secure = load_lottieurl(
            "https://lottie.host/ef003e80-0e69-436f-a632-aae38a02366d/PTzpA1SW3j.json"
        )
        if lottie_secure:
            st_lottie(lottie_secure, height=340, key="secure")

    st.markdown('<div class="ml-divider"></div>', unsafe_allow_html=True)
    st.markdown(
        '<p style="color:#8899bb;font-size:14px;">For dataset and feature details, expand the section below.</p>',
        unsafe_allow_html=True,
    )

    with st.expander("Project Details - Dataset, Features & Results"):
        _render_html(
            """
        <div class="dataset-card">
            <div class="dataset-title">Dataset Details</div>
            <p style="color:#8899bb;font-size:14px;line-height:1.7;">
                Phishing websites sourced from <b style="color:#f0f6ff;">phishtank.org</b> and
                legitimate websites from <b style="color:#f0f6ff;">tranco-list.eu</b>.<br><br>
                <b style="color:#00c9b1;">31,600 total websites</b> -
                <b style="color:#f0f6ff;">16,100 Legitimate</b> |
                <b style="color:#ff4d6d;">15,500 Phishing</b>
            </p>
        </div>
        """
        )

        c1, c2 = st.columns(2)
        with c1:
            try:
                st.image(Image.open("images/piechart.png"), width="stretch")
            except Exception:
                st.info("piechart.png not found")
        with c2:
            try:
                st.image(Image.open("images/bargraph.png"), width="stretch")
            except Exception:
                st.info("bargraph.png not found")

        number = st.slider("Select rows to preview", 0, 100, 5)
        st.dataframe(ml.legitimate_df.head(number), width="stretch")

        @st.cache_data
        def convert_df(df):
            return df.to_csv().encode("utf-8")

        st.download_button(
            label="Download Dataset as CSV",
            data=convert_df(ml.df),
            file_name="phishing_legitimate_structured_data.csv",
            mime="text/csv",
        )
        st.table(ml.df_results)

    st.markdown('<div class="ml-divider"></div>', unsafe_allow_html=True)
    _render_html(
        """
    <div class="section-badge">Detection Engine</div>
    <div class="section-title" style="font-size:28px;">Analyse a <span>URL</span></div>
    <p class="section-sub" style="margin-bottom:28px;">
        Select a model, paste a URL, and let the engine decide - legitimate or phishing.
    </p>
    """
    )

    choice = st.selectbox(
        "Select ML Model",
        [
            "SVM",
            "Decision Tree",
            "Random Forest",
            
            
        ],
    )

    model_map = {
        "SVM": ml.xgb_model,
        "Decision Tree": ml.dt_model,
        "Random Forest": ml.rf_model,  
        
    }
    model = model_map.get(choice)

    st.markdown(
        f'<p style="color:#00c9b1;font-size:13px;margin:8px 0 20px;">Model selected: {choice}</p>',
        unsafe_allow_html=True,
    )

    url = st.text_input("Enter complete URL", placeholder="https://website.xyz")

    col_btn, _ = st.columns([1, 3])
    with col_btn:
        check = st.button("Analyse URL", width="stretch")

    if check:
        if not url:
            st.warning("Please enter a URL first.")
            return

        if model is None:
            st.error("Selected model is not available.")
            return

        with st.spinner("Fetching and analysing the page..."):
            try:
                headers = {"User-Agent": "Mozilla/5.0"}
                response = requests.get(url, verify=False, timeout=5, headers=headers, allow_redirects=True)

                from urllib.parse import urlparse

                original_domain = urlparse(url).netloc.lower().replace("www.", "")
                final_domain = urlparse(response.url).netloc.lower().replace("www.", "")
                redirected_away = original_domain != final_domain

                if response.status_code >= 500:
                    _render_html(
                        f"""
                    <div class="result-warn">
                        <div class="result-warn-title">Server Error</div>
                        <p style="color:#8899bb;">Status {response.status_code} - server is not responding correctly.</p>
                    </div>
                    """
                    )
                    return

                if response.status_code == 404:
                    _render_html(
                        f"""
                    <div class="result-warn">
                        <div class="result-warn-title">404 - Page Not Found</div>
                        <p style="color:#8899bb;">This path no longer exists on <b style="color:#f0f6ff;">{final_domain}</b>.</p>
                    </div>
                    """
                    )
                    return

                if not response.content or len(response.content) < 10:
                    _render_html(
                        """
                    <div class="result-warn">
                        <div class="result-warn-title">Empty Page</div>
                        <p style="color:#8899bb;">The page returned no content. Cannot analyse.</p>
                    </div>
                    """
                    )
                    return

                soup = BeautifulSoup(response.content, "html.parser")
                vector = _vector_for_model(model, soup)
                result = model.predict(vector)

                legit_pct = phish_pct = None
                if hasattr(model, "predict_proba"):
                    proba = model.predict_proba(vector)[0]
                    legit_pct = round(float(proba[0]) * 100, 1)
                    phish_pct = round(float(proba[1]) * 100, 1)

                redirect_note = (
                    f'<div class="redirect-note">&#x21AA; Redirected from <b>{original_domain}</b> &#8594; <b>{final_domain}</b></div>'
                    if redirected_away
                    else ""
                )

                if result[0] == 0:
                    if legit_pct is not None and phish_pct is not None:
                        _render_html(
                            f"""
                        <div class="result-modal modal-safe">
                            <div style="position:relative;z-index:1;">
                                <div class="modal-icon icon-safe">&#x2705;</div>
                                <div class="modal-title modal-title-safe">This Website is Legitimate</div>
                                <p class="modal-desc">
                                    Our ML model found no phishing indicators on this page.
                                    The content appears to be from a <b style="color:#f0f6ff;">trusted, legitimate source</b>.
                                </p>{redirect_note}
                                <div style="display:flex;align-items:center;gap:16px;margin:20px 0;flex-wrap:wrap;">
                                    <div style="background:rgba(0,230,118,0.12);border:1px solid rgba(0,230,118,0.35);border-radius:16px;padding:18px 28px;text-align:center;min-width:130px;">
                                        <div style="font-family:Syne,sans-serif;font-size:42px;font-weight:800;color:#00e676;line-height:1;">{legit_pct}%</div>
                                        <div style="font-size:11px;color:#8899bb;letter-spacing:1.5px;text-transform:uppercase;margin-top:6px;">Legitimate Score</div>
                                    </div>
                                    <div style="background:rgba(255,77,109,0.07);border:1px solid rgba(255,77,109,0.2);border-radius:16px;padding:18px 28px;text-align:center;min-width:130px;">
                                        <div style="font-family:Syne,sans-serif;font-size:42px;font-weight:800;color:#ff4d6d;line-height:1;">{phish_pct}%</div>
                                        <div style="font-size:11px;color:#8899bb;letter-spacing:1.5px;text-transform:uppercase;margin-top:6px;">Phishing Score</div>
                                    </div>
                                </div>
                                <div style="margin-bottom:6px;">
                                    <div style="display:flex;justify-content:space-between;font-size:11px;color:#8899bb;margin-bottom:6px;">
                                        <span>&#x2705; Legitimate Confidence</span><span>{legit_pct}%</span>
                                    </div>
                                    <div style="background:rgba(255,255,255,0.05);border-radius:50px;height:10px;overflow:hidden;">
                                        <div style="width:{legit_pct}%;height:10px;border-radius:50px;background:linear-gradient(90deg,#00c9b1,#00e676);box-shadow:0 0 10px rgba(0,230,118,0.5);"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """
                        )
                    else:
                        _render_html(
                            f"""
                        <div class="result-modal modal-safe">
                            <div style="position:relative;z-index:1;">
                                <div class="modal-icon icon-safe">&#x2705;</div>
                                <div class="modal-title modal-title-safe">This Website is Legitimate</div>
                                <p class="modal-desc">No phishing indicators detected.</p>{redirect_note}
                            </div>
                        </div>
                        """
                        )
                    st.balloons()
                else:
                    if legit_pct is not None and phish_pct is not None:
                        _render_html(
                            f"""
                        <div class="result-modal modal-phish">
                            <div style="position:relative;z-index:1;">
                                <div class="modal-icon icon-phish">&#x1F6A8;</div>
                                <div class="modal-title modal-title-phish">Phishing Website Detected!</div>
                                <p class="modal-desc">
                                    This webpage shows <b style="color:#ff4d6d;">strong phishing indicators</b>.
                                    Do <b style="color:#f0f6ff;">NOT</b> enter passwords, credit cards,
                                    or any personal information on this site.
                                </p>{redirect_note}
                                <div style="display:flex;align-items:center;gap:16px;margin:20px 0;flex-wrap:wrap;">
                                    <div style="background:rgba(255,77,109,0.12);border:1px solid rgba(255,77,109,0.35);border-radius:16px;padding:18px 28px;text-align:center;min-width:130px;">
                                        <div style="font-family:Syne,sans-serif;font-size:42px;font-weight:800;color:#ff4d6d;line-height:1;">{phish_pct}%</div>
                                        <div style="font-size:11px;color:#8899bb;letter-spacing:1.5px;text-transform:uppercase;margin-top:6px;">Phishing Confidence</div>
                                    </div>
                                    <div style="background:rgba(0,230,118,0.07);border:1px solid rgba(0,230,118,0.2);border-radius:16px;padding:18px 28px;text-align:center;min-width:130px;">
                                        <div style="font-family:Syne,sans-serif;font-size:42px;font-weight:800;color:#00e676;line-height:1;">{legit_pct}%</div>
                                        <div style="font-size:11px;color:#8899bb;letter-spacing:1.5px;text-transform:uppercase;margin-top:6px;">Legitimate Score</div>
                                    </div>
                                </div>
                                <div style="margin-bottom:6px;">
                                    <div style="display:flex;justify-content:space-between;font-size:11px;color:#8899bb;margin-bottom:6px;">
                                        <span>&#x1F6A8; Phishing Threat</span><span>{phish_pct}%</span>
                                    </div>
                                    <div style="background:rgba(255,255,255,0.05);border-radius:50px;height:10px;overflow:hidden;">
                                        <div style="width:{phish_pct}%;height:10px;border-radius:50px;background:linear-gradient(90deg,#c2185b,#ff4d6d);box-shadow:0 0 10px rgba(255,77,109,0.5);"></div>
                                    </div>
                                </div>
                            </div>
                        </div>
                        """
                        )
                    else:
                        _render_html(
                            f"""
                        <div class="result-modal modal-phish">
                            <div style="position:relative;z-index:1;">
                                <div class="modal-icon icon-phish">&#x1F6A8;</div>
                                <div class="modal-title modal-title-phish">Phishing Website Detected!</div>
                                <p class="modal-desc">This webpage shows strong phishing indicators.</p>{redirect_note}
                            </div>
                        </div>
                        """
                        )
                    st.snow()

            except requests.exceptions.ConnectionError:
                _render_html(
                    """
                <div class="result-warn">
                    <div class="result-warn-title">Connection Failed</div>
                    <p style="color:#8899bb;">Could not connect to the URL.</p>
                </div>
                """
                )
            except requests.exceptions.Timeout:
                _render_html(
                    """
                <div class="result-warn">
                    <div class="result-warn-title">Request Timed Out</div>
                    <p style="color:#8899bb;">The website took too long to respond.</p>
                </div>
                """
                )
            except requests.exceptions.SSLError:
                _render_html(
                    """
                <div class="result-warn">
                    <div class="result-warn-title">SSL Certificate Error</div>
                    <p style="color:#8899bb;">Invalid or self-signed SSL certificate.</p>
                </div>
                """
                )
            except requests.exceptions.MissingSchema:
                _render_html(
                    """
                <div class="result-warn">
                    <div class="result-warn-title">Invalid URL</div>
                    <p style="color:#8899bb;">Make sure the URL starts with http:// or https://.</p>
                </div>
                """
                )
            except requests.exceptions.RequestException as e:
                _render_html(
                    f"""
                <div class="result-warn">
                    <div class="result-warn-title">Request Failed</div>
                    <p style="color:#8899bb;">{str(e)}</p>
                </div>
                """
                )
