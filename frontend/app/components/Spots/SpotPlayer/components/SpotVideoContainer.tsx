import Hls from 'hls.js';
import { observer } from 'mobx-react-lite';
import React from 'react';

import { useStore } from 'App/mstore';

import spotPlayerStore from '../spotPlayerStore';

const base64toblob = (str) => {
  const byteCharacters = atob(str);
  const byteNumbers = new Array(byteCharacters.length);
  for (let i = 0; i < byteCharacters.length; i++) {
    byteNumbers[i] = byteCharacters.charCodeAt(i);
  }
  const byteArray = new Uint8Array(byteNumbers);
  return new Blob([byteArray]);
};

function SpotVideoContainer({
  videoURL,
  streamFile,
}: {
  videoURL: string;
  streamFile?: string;
}) {
  const videoRef = React.useRef<HTMLVideoElement>(null);
  const playbackTime = React.useRef(0);
  const { spotStore } = useStore();
  React.useEffect(() => {
    if (Hls.isSupported() && videoRef.current) {
      if (streamFile) {
        const hls = new Hls({ workerPath: '/hls-worker.js' });
        const url = URL.createObjectURL(base64toblob(streamFile));
        if (url && videoRef.current) {
          hls.loadSource(url);
          hls.attachMedia(videoRef.current);
        } else {
          if (videoRef.current) {
            videoRef.current.src = videoURL;
          }
        }
      } else {
        videoRef.current.src = videoURL;
      }
    }
  }, []);

  React.useEffect(() => {
    if (spotPlayerStore.isPlaying) {
      void videoRef.current?.play();
    } else {
      videoRef.current?.pause();
    }
  }, [spotPlayerStore.isPlaying]);

  React.useEffect(() => {
    const int = setInterval(() => {
      const videoTime = videoRef.current?.currentTime ?? 0;
      if (videoTime !== spotPlayerStore.time) {
        playbackTime.current = videoTime;
        spotPlayerStore.setTime(videoTime);
      }
    }, 100);
    return () => clearInterval(int);
  }, []);

  React.useEffect(() => {
    if (playbackTime.current !== spotPlayerStore.time && videoRef.current) {
      videoRef.current.currentTime = spotPlayerStore.time;
    }
  }, [spotPlayerStore.time]);

  React.useEffect(() => {
    if (videoRef.current) {
      videoRef.current.playbackRate = spotPlayerStore.playbackRate;
    }
  }, [spotPlayerStore.playbackRate]);

  const getTypeFromUrl = (url: string) => {
    const ext = url.split('.').pop();
    if (ext === 'mp4') {
      return 'video/mp4';
    }
    if (ext === 'webm') {
      return 'video/webm';
    }
    if (ext === 'ogg') {
      return 'video/ogg';
    }
    return 'video/mp4';
  };
  return (
    <video
      ref={videoRef}
      className={
        'object-contain absolute top-0 left-0 w-full h-full bg-gray-lightest cursor-pointer'
      }
      onClick={() => spotPlayerStore.setIsPlaying(!spotPlayerStore.isPlaying)}
    />
  );
}

export default observer(SpotVideoContainer);
