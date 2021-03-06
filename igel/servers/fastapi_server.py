import logging
import os
from pathlib import Path

import pandas as pd
import uvicorn
from fastapi import Body, FastAPI
from igel import Igel
from igel.configs import temp_post_req_data_path
from igel.constants import Constants

try:
    from .helper import remove_temp_data_file
except ImportError:
    from igel.servers.helper import remove_temp_data_file


logger = logging.getLogger(__name__)


app = FastAPI()


@app.get("/")
async def just_for_testing():
    return {"success": True}


@app.post("/predict")
async def predict(data: dict = Body(...)):
    """
    parse json data received from client, use pre-trained model to generate predictions and send them back to client
    """
    try:
        logger.info(
            f"received request successfully, data will be parsed and used as inputs to generate predictions"
        )

        # convert values to list in order to convert it later to pandas dataframe
        data = {
            k: [v] if not isinstance(v, list) else v for k, v in data.items()
        }

        # convert received data to dataframe
        df = pd.DataFrame(data, index=None)
        df.to_csv(temp_post_req_data_path, index=False)

        # use igel to generate predictions
        model_resutls_path = os.environ.get(Constants.model_results_path)
        logger.info(f"model_results path: {model_resutls_path}")

        if not model_resutls_path:
            logger.warning(
                f"Please provide path to the model_results directory generated by igel using the cli!"
            )
        else:
            model_path = Path(model_resutls_path) / Constants.model_file
            description_file = (
                Path(model_resutls_path) / Constants.description_file
            )
            prediction_file = (
                Path(model_resutls_path) / Constants.prediction_file
            )

            res = Igel(
                cmd="predict",
                data_path=str(temp_post_req_data_path),
                model_path=model_path,
                description_file=description_file,
                prediction_file=prediction_file,
            )

            # remove temp file:
            remove_temp_data_file(temp_post_req_data_path)

            logger.info("sending predictions back to client...")
            return {"prediction": res.predictions.to_numpy().tolist()}

    except FileNotFoundError as ex:
        remove_temp_data_file(temp_post_req_data_path)
        logger.exception(ex)


def run(**kwargs):

    uvicorn.run(app, **kwargs)


if __name__ == "__main__":
    run()
