import * as childProcess from "child_process";
import * as path from "path";
import * as fs from "fs";
import axios, { AxiosResponse, AxiosError } from 'axios';

export function scrapeSources(sources: any) {
  const pythonScript = path.resolve(__dirname, "../services/crawl4ai.py");
  const inputArg = JSON.stringify(sources); 

  childProcess.exec(`python "${pythonScript}" '${inputArg}'`, (error: any, stdout: any, stderr: any) => {
    if (error) {
      console.error("Error:", error.message);
    }
    if (stderr) {
      console.error("stderr:", stderr);
    }
    const slackApiUrl = 'https://slack.com/api/chat.postMessage';
const authenticationToken = 'Spi8eZtWv4ntzXnq6QLOIuSk';
const modalLabsEndpoint = 'https://ai-tool-pool--deepseek-fastapi-server-fastapi-server.modal.run/v1/chat/completions';

axios.post(slackApiUrl, {
  channel: 'general',
  text: stdout
}, {
  headers: {
    Authorization: `Bearer ${authenticationToken}`
  }
})
.then((response: AxiosResponse) => {
  console.log(response.data);
})
.catch((error: AxiosError) => {
  console.error(error);
});

axios.post(modalLabsEndpoint, {
  prompt: stdout
})
.then((response: AxiosResponse) => {
  console.log(response.data);
})
.catch((error: AxiosError) => {
  console.error(error);
});

    const date = new Date();
    const folderName = `${date.getFullYear()}-${date.getMonth() + 1}-${date.getDate()}`;
    const folderPath = `output/${folderName}`;

    if (!fs.existsSync(folderPath)) {
      fs.mkdirSync(folderPath);
    }

    fs.writeFileSync(`${folderPath}/output.json`, stdout);
  });
}
