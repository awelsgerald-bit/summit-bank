import { useEffect, useRef, useState } from 'react';

export default function useCountUp(value, duration = 900) {
  const [display, setDisplay] = useState(value);
  const [flashing, setFlashing] = useState(false);
  const prevRef = useRef(value);

  useEffect(() => {
    const from = prevRef.current;
    const to = value;

    if (from === to) {
      setDisplay(to);
      return;
    }

    let start;
    setFlashing(true);

    function tick(ts) {
      if (!start) start = ts;
      const t = Math.min(1, (ts - start) / duration);
      const eased = 1 - Math.pow(1 - t, 3);
      setDisplay(from + (to - from) * eased);
      if (t < 1) {
        requestAnimationFrame(tick);
      } else {
        setDisplay(to);
        prevRef.current = to;
        setTimeout(() => setFlashing(false), 400);
      }
    }
    requestAnimationFrame(tick);
  }, [value, duration]);

  return [display, flashing];
}