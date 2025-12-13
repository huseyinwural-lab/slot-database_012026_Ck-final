import React from 'react';
import { useParams } from 'react-router-dom';

const GameRoom = () => {
  const { id } = useParams();

  // In a real app, fetch game launch URL from backend
  // GET /api/v1/games/{id}/launch
  
  return (
    <div className="h-[80vh] w-full bg-black rounded-xl overflow-hidden border border-white/10 relative flex items-center justify-center">
        <div className="absolute inset-0 bg-secondary flex flex-col items-center justify-center text-muted-foreground">
            <p className="text-xl font-bold mb-2">Game Container</p>
            <p className="font-mono text-sm">Game ID: {id}</p>
            <p className="text-xs mt-4">In production, an iframe would load here.</p>
        </div>
        
        {/* Mock Iframe */}
        {/* <iframe src={launchUrl} className="w-full h-full border-0" allowFullScreen /> */}
    </div>
  );
};

export default GameRoom;