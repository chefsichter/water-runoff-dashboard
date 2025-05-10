import numpy as np
import pandas as pd
import joblib
import torch
import shap

STATIC_FEATURES = [
    'abb', 'area', 'atb', 'btk', 'dhm', 'glm', 'kwt', 'pfc',
    'frac_water', 'frac_urban_areas', 'frac_coniferous_forests',
    'frac_deciduous_forests', 'frac_mixed_forests', 'frac_cereals',
    'frac_pasture', 'frac_bush', 'frac_unknown', 'frac_firn',
    'frac_bare_ice', 'frac_rock', 'frac_vegetables',
    'frac_alpine_vegetation', 'frac_wetlands',
    'frac_sub_Alpine_meadow', 'frac_alpine_meadow',
    'frac_bare_soil_vegetation', 'frac_grapes', 'slp'
]

DYNAMIC_FEATURES = ['P', 'T']
TIME_FEATURE = 'time'


class StaticSensitivity:
    """Class to perform static sensitivity analysis."""
    def __init__(self,
                 scaler_path="data/model/scaler.pkl",
                 model_path="data/model/model.pt",
                 sample_path="data/model/sample_tensor.pt"):
        self.scaler = joblib.load(scaler_path)
        self.model = torch.jit.load(model_path)
        self.model.eval()
        self.sample = torch.load(sample_path)
        self.explainer = shap.GradientExplainer(self.model, self.sample)
        self.features = DYNAMIC_FEATURES + STATIC_FEATURES + [TIME_FEATURE]

    def analyze(self, df_input: pd.DataFrame) -> pd.DataFrame:
        df = df_input.copy()

        assert set(self.features).issubset(df.columns)

        df = df[self.features]
        df['year'] = df[TIME_FEATURE].dt.year
        df['day_of_year'] = df[TIME_FEATURE].dt.dayofyear
        df.drop(TIME_FEATURE, axis=1, inplace=True)

        df['Y'] = 0.0
        df_scaled = pd.DataFrame(self.scaler.transform(df), columns=df.columns)
        df_scaled.drop("Y", axis=1, inplace=True)
        tensor = torch.tensor(df_scaled.to_numpy())

        shap_values = self.explainer.shap_values(tensor, nsamples=1000, rseed=42)
        shap_values = np.squeeze(shap_values, axis=2)

        df_shape = pd.DataFrame(shap_values, columns=df_scaled.columns)
        df_avg = df_shape.mean().abs()
        df_abs = df_avg.abs()
        df_norm = df_abs / df_abs.sum() * 100
        signed_norm = [np.sign(df_avg) * df_norm]
        df_output = pd.DataFrame(signed_norm, columns=df_scaled.columns)

        return df_output


class RNNSensitivity:
    """
    Class for RNN model SHAP sensitivity analysis over 7-day sequences.
    """

    def __init__(self,
                 scaler_static_path="data/model/scaler_static_rnn.pkl",
                 scaler_dynamic_path="data/model/scaler_dynamic_rnn.pkl",
                 model_path="data/model/model_rnn.pt",
                 sample_path="data/model/sample_tensor_rnn.pt"):
        self.scaler_static = joblib.load(scaler_static_path)
        self.scaler_dynamic = joblib.load(scaler_dynamic_path)
        self.model_rnn = torch.jit.load(model_path)
        self.model_rnn.eval()
        sampled_static, sampled_dynamic = torch.load(sample_path)
        # prepare background for SHAP
        n_samples, n_static = sampled_static.shape
        dynamic_unraveled = sampled_dynamic.reshape(n_samples, n_static)
        background = torch.cat([sampled_static, dynamic_unraveled], dim=1)

        # define wrapped model
        class WrappedModel(torch.nn.Module):
            def __init__(self, model, n_static):
                super().__init__()
                self.model = model
                self.n_static = n_static

            def forward(self, x):
                static = x[:, :self.n_static]
                dynamic = x[:, self.n_static:].reshape(x.shape[0], 7, 4)
                return self.model(static, dynamic)

        self.wrapped = WrappedModel(self.model_rnn, n_static)
        self.explainer = shap.GradientExplainer(self.wrapped, background)
        self.features_static = STATIC_FEATURES
        # dynamic feature names: P_i, T_i, time_i for i=6..0
        self.features_dynamic = []
        for i in range(6, -1, -1):
            # dynamic sequence features: P_i, T_i and time_i
            self.features_dynamic.extend([f'P_{i}', f'T_{i}', f'{TIME_FEATURE}_{i}'])
        self.features = self.features_static + self.features_dynamic

    def analyze(self, df_input: pd.DataFrame) -> pd.DataFrame:
        assert set(self.features).issubset(df_input.columns)
        df = df_input[self.features].copy()

        # extract dynamic time features (als float casten, um spätere Skalierung ohne dtype-Konflikt zu ermöglichen)
        for i in range(6, -1, -1):
            df[f'year_{i}'] = df[f'{TIME_FEATURE}_{i}'].dt.year.astype(float)
            df[f'day_of_year_{i}'] = df[f'{TIME_FEATURE}_{i}'].dt.dayofyear.astype(float)
        df.drop(columns=[f'{TIME_FEATURE}_{i}' for i in range(6, -1, -1)], inplace=True)
        df['Y'] = 0.0

        # scale dynamic windows (bypass feature name validation by using numpy arrays)
        for i in range(6, -1, -1):
            cols = [f'P_{i}', f'T_{i}', f'year_{i}', f'day_of_year_{i}', 'Y']
            arr = df[cols].to_numpy()
            scaled = self.scaler_dynamic.transform(arr)
            df.loc[:, cols] = scaled

        # scale static
        df[self.features_static] = pd.DataFrame(
            self.scaler_static.transform(df[self.features_static]),
            columns=self.features_static
        )

        df.drop("Y", axis=1, inplace=True)

        tensor = torch.tensor(df.to_numpy())

        shap_values = self.explainer.shap_values(tensor, nsamples=1000, rseed=42)
        shap_values = np.squeeze(shap_values, axis=2)

        df_shape = pd.DataFrame(shap_values, columns=df.columns)
        df_avg = df_shape.mean().abs()
        df_abs = df_avg.abs()
        df_norm = df_abs / df_abs.sum() * 100
        signed_norm = [np.sign(df_avg) * df_norm]
        df_output = pd.DataFrame(signed_norm, columns=df.columns)

        return df_output
