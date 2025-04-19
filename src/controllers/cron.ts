import * as cron from "node-cron";
import * as fs from "fs";
import { scrapeSources } from "../services/scrapeSources";

export function handleCron() {
  cron.schedule("*/1 * * * *", () => {
    const sources = JSON.parse(fs.readFileSync("src/data/sources.json", "utf8"));
    scrapeSources(sources);
  });
}
