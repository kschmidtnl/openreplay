import { resentOrDate, shortDurationFromMs } from "App/date";

export class Spot {
  thumbnail: string;
  title: string;
  createdAt: string;
  user: string;
  duration: string;
  spotId: number;
  mobURL?: string;
  videoURL?: string;
  comments?: { user: string, text: string, createdAt: string }[] = []
  /** public access key to add to url */
  key?: { key: string, expirationDate: string } | null = null


  constructor(data: Record<string, any>) {
    this.thumbnail = data.previewURL
    this.title = data.name;
    this.createdAt = resentOrDate(new Date(data.createdAt).getTime());
    this.user = data.userEmail;
    this.duration = shortDurationFromMs(data.duration);
    this.spotId = data.id

    this.setAdditionalData(data)
  }

  setAdditionalData(data: Record<string, any>) {
    Object.assign(this, data)
  }
}
