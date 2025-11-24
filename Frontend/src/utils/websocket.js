import { useEffect, useRef, useState } from 'react';

export const useWebSocket = (url) => {
  const [lastMessage, setLastMessage] = useState(null);
  const [readyState, setReadyState] = useState(0);
  const ws = useRef(null);

  useEffect(() => {
    ws.current = new WebSocket(url);
    
    ws.current.onopen = () => {
      console.log('WebSocket connected');
      setReadyState(1);
    };
    
    ws.current.onclose = () => {
      console.log('WebSocket disconnected');
      setReadyState(3);
    };
    
    ws.current.onerror = (error) => {
      console.error('WebSocket error:', error);
      setReadyState(3);
    };
    
    ws.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      } catch (error) {
        console.error('WebSocket message error:', error);
      }
    };

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, [url]);

  return { lastMessage, readyState };
};