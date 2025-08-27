import express from 'express';
import path from 'path';
import fetch from 'node-fetch';
import { fileURLToPath } from 'url';

const app = express();
const port = 3000;

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

app.use(express.static(__dirname));

app.get('/api/data', async (req, res) => {
  try {
    const fluxQuery = `
      from(bucket:"SmartHome")
      |> range(start: -10m)
      |> filter(fn: (r) => r._measurement == "sensor_data")
      |> sort(columns: ["_time"], desc: true)
      |> limit(n: 20)
    `;

    const influxRes = await fetch("https://us-east-1-1.aws.cloud2.influxdata.com/api/v2/query?org=HelloCode%20Team", {
      method: "POST",
      headers: {
        "Authorization": "Token E1gldyRvV5_yQ7Gdj3z5LepQPZR6pDkVn2s8MmVr4srBhADlztOQrtkveF5Q8nIlNS6_6yVyUEdNDavl06zmIQ==",
        "Content-Type": "application/vnd.flux",
        "Accept": "text/csv"
      },
      body: fluxQuery
    });

    const text = await influxRes.text();
    res.send(text);
  } catch (err) {
    console.error("[PROXY ERROR]", err);
    res.status(500).send("Fetch failed");
  }
});

app.listen(port, () => {
  console.log(`🌐 Dashboard running at: http://localhost:${port}`);
});
