import React, { useEffect, useState } from 'react';
import api from '../services/api';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import { Send, User } from 'lucide-react';

const Support = () => {
  const [tickets, setTickets] = useState([]);
  const [selectedTicket, setSelectedTicket] = useState(null);
  const [reply, setReply] = useState("");

  const fetchTickets = async () => {
    try {
        const res = await api.get('/v1/tickets');
        setTickets(res.data);
    } catch (err) {
        console.error(err);
    }
  };

  useEffect(() => { fetchTickets(); }, []);

  const handleReply = async () => {
    if (!selectedTicket || !reply) return;
    try {
        const msg = { sender: 'admin', text: reply };
        await api.post(`/v1/tickets/${selectedTicket.id}/reply`, msg);
        
        // Update local state optimistic
        const updated = { 
            ...selectedTicket, 
            messages: [...selectedTicket.messages, { ...msg, timestamp: new Date().toISOString() }] 
        };
        setSelectedTicket(updated);
        setTickets(tickets.map(t => t.id === updated.id ? updated : t));
        setReply("");
        toast.success("Reply sent");
    } catch (err) {
        toast.error("Failed to send reply");
    }
  };

  return (
    <div className="h-[calc(100vh-100px)] flex gap-6">
        {/* Ticket List */}
        <Card className="w-1/3 flex flex-col">
            <CardHeader><CardTitle>Tickets</CardTitle></CardHeader>
            <ScrollArea className="flex-1">
                <div className="space-y-2 p-4 pt-0">
                    {tickets.map(ticket => (
                        <div 
                            key={ticket.id}
                            onClick={() => setSelectedTicket(ticket)}
                            className={`p-4 rounded-lg border cursor-pointer hover:bg-secondary/50 transition-colors ${selectedTicket?.id === ticket.id ? 'bg-secondary border-primary' : 'bg-card'}`}
                        >
                            <div className="flex justify-between items-start mb-1">
                                <span className="font-semibold">{ticket.subject}</span>
                                <Badge variant={ticket.status === 'open' ? 'default' : 'secondary'}>{ticket.status}</Badge>
                            </div>
                            <p className="text-sm text-muted-foreground truncate">{ticket.player_username}</p>
                        </div>
                    ))}
                </div>
            </ScrollArea>
        </Card>

        {/* Chat Area */}
        <Card className="flex-1 flex flex-col">
            {selectedTicket ? (
                <>
                    <CardHeader className="border-b">
                        <CardTitle className="flex justify-between">
                            <span>{selectedTicket.subject}</span>
                            <span className="text-sm font-normal text-muted-foreground">ID: {selectedTicket.id}</span>
                        </CardTitle>
                    </CardHeader>
                    <ScrollArea className="flex-1 p-4">
                        <div className="space-y-4">
                            {selectedTicket.messages.map((msg, i) => (
                                <div key={i} className={`flex ${msg.sender === 'admin' ? 'justify-end' : 'justify-start'}`}>
                                    <div className={`max-w-[80%] rounded-lg p-3 ${msg.sender === 'admin' ? 'bg-primary text-primary-foreground' : 'bg-secondary'}`}>
                                        <p className="text-sm">{msg.text}</p>
                                        <span className="text-[10px] opacity-70 mt-1 block">
                                            {new Date(msg.timestamp).toLocaleTimeString()}
                                        </span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </ScrollArea>
                    <div className="p-4 border-t flex gap-2">
                        <Input 
                            value={reply} 
                            onChange={e => setReply(e.target.value)} 
                            placeholder="Type your reply..." 
                            onKeyDown={e => e.key === 'Enter' && handleReply()}
                        />
                        <Button size="icon" onClick={handleReply}><Send className="w-4 h-4" /></Button>
                    </div>
                </>
            ) : (
                <div className="flex-1 flex items-center justify-center text-muted-foreground">
                    Select a ticket to view details
                </div>
            )}
        </Card>
    </div>
  );
};

export default Support;
