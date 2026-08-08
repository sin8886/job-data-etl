from clean import run_pipeline, DEFAULT_OUTPUT


def transform(input_path):

    df = run_pipeline(input_path, DEFAULT_OUTPUT)

    return df
