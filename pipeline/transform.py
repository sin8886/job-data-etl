from clean import DEFAULT_OUTPUT, run_pipeline


def transform(input_path):

    df = run_pipeline(input_path, DEFAULT_OUTPUT)

    return df
