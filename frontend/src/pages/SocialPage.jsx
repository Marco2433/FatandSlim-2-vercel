import { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/context/AuthContext';
import axios from 'axios';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Textarea } from '@/components/ui/textarea';
import { Badge } from '@/components/ui/badge';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter, DialogDescription } from '@/components/ui/dialog';
import { ScrollArea } from '@/components/ui/scroll-area';
import { toast } from 'sonner';
import { 
  Users, 
  Search, 
  UserPlus, 
  MessageCircle, 
  Bell, 
  Trophy, 
  Heart,
  Send,
  ArrowLeft,
  Check,
  X,
  Loader2,
  Home,
  Crown,
  Medal,
  Star,
  Plus,
  Image as ImageIcon,
  Swords,
  ChevronRight
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

export default function SocialPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('feed');
  const [loading, setLoading] = useState(true);
  
  // Data states
  const [feed, setFeed] = useState([]);
  const [friends, setFriends] = useState([]);
  const [friendRequests, setFriendRequests] = useState({ received: [], sent: [] });
  const [conversations, setConversations] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [leaderboard, setLeaderboard] = useState([]);
  const [groups, setGroups] = useState([]);
  const [challenges, setChallenges] = useState([]);
  
  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  
  // Dialogs
  const [showMessageDialog, setShowMessageDialog] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  const [showPostDialog, setShowPostDialog] = useState(false);
  const [newPost, setNewPost] = useState('');
  const [showProfileDialog, setShowProfileDialog] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState(null);
  const [showChallengeDialog, setShowChallengeDialog] = useState(false);
  const [challengeConfig, setChallengeConfig] = useState({ type: 'steps', target: 10000, duration_days: 7 });
  const [challengeFriend, setChallengeFriend] = useState(null);

  // Fetch all data
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [feedRes, friendsRes, requestsRes, convsRes, notifsRes, leaderRes, groupsRes, challengesRes] = await Promise.allSettled([
        axios.get(`${API}/social/feed`, { withCredentials: true }),
        axios.get(`${API}/social/friends`, { withCredentials: true }),
        axios.get(`${API}/social/friends/requests`, { withCredentials: true }),
        axios.get(`${API}/social/messages`, { withCredentials: true }),
        axios.get(`${API}/social/notifications`, { withCredentials: true }),
        axios.get(`${API}/social/leaderboard`, { withCredentials: true }),
        axios.get(`${API}/social/groups`, { withCredentials: true }),
        axios.get(`${API}/social/challenges`, { withCredentials: true })
      ]);
      
      if (feedRes.status === 'fulfilled') setFeed(feedRes.value.data.activities || []);
      if (friendsRes.status === 'fulfilled') setFriends(friendsRes.value.data.friends || []);
      if (requestsRes.status === 'fulfilled') setFriendRequests(requestsRes.value.data);
      if (convsRes.status === 'fulfilled') setConversations(convsRes.value.data.conversations || []);
      if (notifsRes.status === 'fulfilled') setNotifications(notifsRes.value.data.notifications || []);
      if (leaderRes.status === 'fulfilled') setLeaderboard(leaderRes.value.data.leaderboard || []);
      if (groupsRes.status === 'fulfilled') setGroups(groupsRes.value.data.groups || []);
      if (challengesRes.status === 'fulfilled') setChallenges(challengesRes.value.data.challenges || []);
    } catch (error) {
      console.error('Error fetching social data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Search users
  const handleSearch = async () => {
    if (searchQuery.length < 2) return;
    setSearching(true);
    try {
      const response = await axios.get(`${API}/social/search?q=${encodeURIComponent(searchQuery)}`, { withCredentials: true });
      setSearchResults(response.data.users || []);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setSearching(false);
    }
  };

  // Friend actions
  const sendFriendRequest = async (friendId) => {
    try {
      await axios.post(`${API}/social/friends/request`, { friend_id: friendId }, { withCredentials: true });
      toast.success('Demande envoyée !');
      handleSearch();
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur');
    }
  };

  const acceptRequest = async (friendshipId) => {
    try {
      await axios.post(`${API}/social/friends/accept`, { friendship_id: friendshipId }, { withCredentials: true });
      toast.success('Ami ajouté !');
      fetchData();
    } catch (error) {
      toast.error('Erreur');
    }
  };

  const rejectRequest = async (friendshipId) => {
    try {
      await axios.post(`${API}/social/friends/reject`, { friendship_id: friendshipId }, { withCredentials: true });
      fetchData();
    } catch (error) {
      toast.error('Erreur');
    }
  };

  // Messages
  const openConversation = async (partnerId, partnerName, partnerPicture) => {
    setSelectedConversation({ partner_id: partnerId, partner_name: partnerName, partner_picture: partnerPicture });
    try {
      const response = await axios.get(`${API}/social/messages/${partnerId}`, { withCredentials: true });
      setMessages(response.data.messages || []);
      setShowMessageDialog(true);
    } catch (error) {
      toast.error('Erreur');
    }
  };

  const sendMessage = async () => {
    if (!newMessage.trim() || !selectedConversation) return;
    try {
      await axios.post(`${API}/social/messages`, {
        recipient_id: selectedConversation.partner_id,
        content: newMessage.trim()
      }, { withCredentials: true });
      setNewMessage('');
      const response = await axios.get(`${API}/social/messages/${selectedConversation.partner_id}`, { withCredentials: true });
      setMessages(response.data.messages || []);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur');
    }
  };

  // Posts
  const createPost = async () => {
    if (!newPost.trim()) return;
    try {
      await axios.post(`${API}/social/post`, { content: newPost.trim(), type: 'text' }, { withCredentials: true });
      setNewPost('');
      setShowPostDialog(false);
      toast.success('Publié !');
      fetchData();
    } catch (error) {
      toast.error('Erreur');
    }
  };

  const likePost = async (activityId) => {
    try {
      await axios.post(`${API}/social/like/${activityId}`, {}, { withCredentials: true });
      fetchData();
    } catch (error) {
      toast.error('Erreur');
    }
  };

  // Profile
  const viewProfile = async (userId) => {
    try {
      const response = await axios.get(`${API}/social/profile/${userId}`, { withCredentials: true });
      setSelectedProfile(response.data);
      setShowProfileDialog(true);
    } catch (error) {
      toast.error('Erreur');
    }
  };

  // Groups
  const toggleGroup = async (groupId, isMember) => {
    try {
      if (isMember) {
        await axios.post(`${API}/social/groups/leave`, { group_id: groupId }, { withCredentials: true });
        toast.success('Groupe quitté');
      } else {
        await axios.post(`${API}/social/groups/join`, { group_id: groupId }, { withCredentials: true });
        toast.success('Groupe rejoint !');
      }
      fetchData();
    } catch (error) {
      toast.error('Erreur');
    }
  };

  // Challenges
  const createChallenge = async () => {
    if (!challengeFriend) return;
    try {
      await axios.post(`${API}/social/challenges/create`, {
        friend_id: challengeFriend.user_id,
        ...challengeConfig
      }, { withCredentials: true });
      toast.success('Défi envoyé !');
      setShowChallengeDialog(false);
      setChallengeFriend(null);
      fetchData();
    } catch (error) {
      toast.error('Erreur');
    }
  };

  const acceptChallenge = async (challengeId) => {
    try {
      await axios.post(`${API}/social/challenges/${challengeId}/accept`, {}, { withCredentials: true });
      toast.success('Défi accepté !');
      fetchData();
    } catch (error) {
      toast.error('Erreur');
    }
  };

  // Mark notifications as read
  const markNotificationsRead = async () => {
    try {
      await axios.post(`${API}/social/notifications/read`, {}, { withCredentials: true });
      fetchData();
    } catch (error) {
      console.error(error);
    }
  };

  const unreadNotifs = notifications.filter(n => !n.read).length;

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <Loader2 className="w-8 h-8 animate-spin text-primary" />
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background pb-safe">
      {/* Header */}
      <header className="sticky top-0 z-10 px-4 py-3 bg-background/80 backdrop-blur-lg border-b border-border">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <Button variant="ghost" size="icon" onClick={() => navigate('/dashboard')}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-lg font-bold">Communauté</h1>
              <p className="text-xs text-muted-foreground">{friends.length} amis</p>
            </div>
          </div>
          <div className="flex gap-2">
            <Button variant="ghost" size="icon" className="relative" onClick={() => { setActiveTab('notifications'); markNotificationsRead(); }}>
              <Bell className="w-5 h-5" />
              {unreadNotifs > 0 && (
                <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-xs text-white flex items-center justify-center">{unreadNotifs}</span>
              )}
            </Button>
          </div>
        </div>
      </header>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full">
        <TabsList className="w-full grid grid-cols-5 h-12 mx-0 rounded-none border-b">
          <TabsTrigger value="feed" className="text-xs"><Home className="w-4 h-4" /></TabsTrigger>
          <TabsTrigger value="friends" className="text-xs"><Users className="w-4 h-4" /></TabsTrigger>
          <TabsTrigger value="messages" className="text-xs relative">
            <MessageCircle className="w-4 h-4" />
            {conversations.filter(c => c.unread_count > 0).length > 0 && (
              <span className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full text-[10px] text-white flex items-center justify-center">
                {conversations.filter(c => c.unread_count > 0).length}
              </span>
            )}
          </TabsTrigger>
          <TabsTrigger value="leaderboard" className="text-xs"><Trophy className="w-4 h-4" /></TabsTrigger>
          <TabsTrigger value="groups" className="text-xs"><Star className="w-4 h-4" /></TabsTrigger>
        </TabsList>

        {/* Feed Tab */}
        <TabsContent value="feed" className="p-4 space-y-4">
          {/* Post Button */}
          <Button className="w-full" onClick={() => setShowPostDialog(true)}>
            <Plus className="w-4 h-4 mr-2" /> Publier quelque chose
          </Button>

          {/* Friend Requests Alert */}
          {friendRequests.received.length > 0 && (
            <Card className="border-primary/50 bg-primary/5">
              <CardContent className="p-4">
                <p className="font-medium mb-2">📬 {friendRequests.received.length} demande(s) d'ami</p>
                <div className="space-y-2">
                  {friendRequests.received.slice(0, 3).map(req => (
                    <div key={req.friendship_id} className="flex items-center justify-between">
                      <div className="flex items-center gap-2">
                        <Avatar className="w-8 h-8">
                          <AvatarImage src={req.picture} />
                          <AvatarFallback>{req.name?.[0]}</AvatarFallback>
                        </Avatar>
                        <span className="text-sm">{req.name}</span>
                      </div>
                      <div className="flex gap-1">
                        <Button size="sm" variant="default" onClick={() => acceptRequest(req.friendship_id)}>
                          <Check className="w-4 h-4" />
                        </Button>
                        <Button size="sm" variant="ghost" onClick={() => rejectRequest(req.friendship_id)}>
                          <X className="w-4 h-4" />
                        </Button>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Activity Feed */}
          {feed.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <Users className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Ajoutez des amis pour voir leur activité !</p>
              </CardContent>
            </Card>
          ) : (
            feed.map(activity => (
              <Card key={activity.activity_id}>
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    <Avatar className="w-10 h-10 cursor-pointer" onClick={() => viewProfile(activity.user_id)}>
                      <AvatarImage src={activity.user_picture} />
                      <AvatarFallback>{activity.user_name?.[0]}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1">
                      <p className="font-medium text-sm">{activity.user_name}</p>
                      <p className="text-xs text-muted-foreground">{new Date(activity.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</p>
                      <p className="mt-2">{activity.content}</p>
                      <div className="flex items-center gap-4 mt-3">
                        <Button variant="ghost" size="sm" onClick={() => likePost(activity.activity_id)} className={activity.user_liked ? 'text-red-500' : ''}>
                          <Heart className={`w-4 h-4 mr-1 ${activity.user_liked ? 'fill-current' : ''}`} />
                          {activity.likes_count || 0}
                        </Button>
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        {/* Friends Tab */}
        <TabsContent value="friends" className="p-4 space-y-4">
          {/* Search */}
          <div className="flex gap-2">
            <Input placeholder="Rechercher des utilisateurs..." value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && handleSearch()} />
            <Button onClick={handleSearch} disabled={searching}>
              {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
            </Button>
          </div>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <Card>
              <CardHeader className="py-2 px-4">
                <CardTitle className="text-sm">Résultats</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {searchResults.map(u => (
                  <div key={u.user_id} className="flex items-center justify-between p-4 border-b last:border-0">
                    <div className="flex items-center gap-3 cursor-pointer" onClick={() => viewProfile(u.user_id)}>
                      <Avatar>
                        <AvatarImage src={u.picture} />
                        <AvatarFallback>{u.name?.[0]}</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium">{u.name}</p>
                        <p className="text-xs text-muted-foreground">{u.email}</p>
                      </div>
                    </div>
                    {u.friendship_status === 'accepted' ? (
                      <Badge>Ami</Badge>
                    ) : u.friendship_status === 'pending' ? (
                      <Badge variant="secondary">En attente</Badge>
                    ) : (
                      <Button size="sm" onClick={() => sendFriendRequest(u.user_id)}>
                        <UserPlus className="w-4 h-4" />
                      </Button>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}

          {/* Friends List */}
          <Card>
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-sm flex items-center justify-between">
                <span>Mes amis ({friends.length})</span>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {friends.length === 0 ? (
                <p className="p-4 text-center text-muted-foreground">Recherchez des amis ci-dessus !</p>
              ) : (
                friends.map(friend => (
                  <div key={friend.user_id} className="flex items-center justify-between p-4 border-b last:border-0">
                    <div className="flex items-center gap-3 cursor-pointer" onClick={() => viewProfile(friend.user_id)}>
                      <Avatar>
                        <AvatarImage src={friend.picture} />
                        <AvatarFallback>{friend.name?.[0]}</AvatarFallback>
                      </Avatar>
                      <div>
                        <p className="font-medium">{friend.name}</p>
                        <p className="text-xs text-muted-foreground">{friend.total_points} pts</p>
                      </div>
                    </div>
                    <div className="flex gap-1">
                      <Button size="sm" variant="ghost" onClick={() => openConversation(friend.user_id, friend.name, friend.picture)}>
                        <MessageCircle className="w-4 h-4" />
                      </Button>
                      <Button size="sm" variant="ghost" onClick={() => { setChallengeFriend(friend); setShowChallengeDialog(true); }}>
                        <Swords className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                ))
              )}
            </CardContent>
          </Card>

          {/* Friend Challenges */}
          {challenges.length > 0 && (
            <Card>
              <CardHeader className="py-3 px-4">
                <CardTitle className="text-sm">⚔️ Défis en cours</CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {challenges.map(c => (
                  <div key={c.challenge_id} className="p-4 border-b last:border-0">
                    <div className="flex items-center justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <Avatar className="w-8 h-8">
                          <AvatarImage src={c.opponent_picture} />
                          <AvatarFallback>{c.opponent_name?.[0]}</AvatarFallback>
                        </Avatar>
                        <span className="font-medium">{c.opponent_name}</span>
                      </div>
                      <Badge variant={c.status === 'active' ? 'default' : 'secondary'}>{c.status === 'pending' ? 'En attente' : 'Actif'}</Badge>
                    </div>
                    <p className="text-sm text-muted-foreground">{c.type === 'steps' ? '🚶 Pas' : c.type === 'meals' ? '🍽️ Repas' : '💪 Workouts'} - Objectif: {c.target}</p>
                    {c.status === 'pending' && !c.is_creator && (
                      <Button size="sm" className="mt-2" onClick={() => acceptChallenge(c.challenge_id)}>Accepter le défi</Button>
                    )}
                  </div>
                ))}
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Messages Tab */}
        <TabsContent value="messages" className="p-4 space-y-4">
          {conversations.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <MessageCircle className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Pas de messages. Discutez avec vos amis !</p>
              </CardContent>
            </Card>
          ) : (
            conversations.map(conv => (
              <Card key={conv.partner_id} className="cursor-pointer hover:bg-muted/50" onClick={() => openConversation(conv.partner_id, conv.partner_name, conv.partner_picture)}>
                <CardContent className="p-4">
                  <div className="flex items-center gap-3">
                    <Avatar>
                      <AvatarImage src={conv.partner_picture} />
                      <AvatarFallback>{conv.partner_name?.[0]}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center justify-between">
                        <p className="font-medium">{conv.partner_name}</p>
                        {conv.unread_count > 0 && (
                          <Badge variant="destructive">{conv.unread_count}</Badge>
                        )}
                      </div>
                      <p className="text-sm text-muted-foreground truncate">{conv.last_message?.content}</p>
                    </div>
                    <ChevronRight className="w-5 h-5 text-muted-foreground" />
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>

        {/* Leaderboard Tab */}
        <TabsContent value="leaderboard" className="p-4 space-y-4">
          <Card>
            <CardHeader className="py-3 px-4">
              <CardTitle className="text-sm flex items-center gap-2">
                <Trophy className="w-5 h-5 text-yellow-500" /> Classement amis
              </CardTitle>
            </CardHeader>
            <CardContent className="p-0">
              {leaderboard.map((entry, index) => (
                <div key={entry.user_id} className={`flex items-center justify-between p-4 border-b last:border-0 ${entry.is_self ? 'bg-primary/5' : ''}`}>
                  <div className="flex items-center gap-3">
                    <div className="w-8 text-center font-bold">
                      {index === 0 ? <Crown className="w-5 h-5 text-yellow-500 mx-auto" /> : index === 1 ? <Medal className="w-5 h-5 text-gray-400 mx-auto" /> : index === 2 ? <Medal className="w-5 h-5 text-amber-600 mx-auto" /> : `#${entry.rank}`}
                    </div>
                    <Avatar>
                      <AvatarImage src={entry.picture} />
                      <AvatarFallback>{entry.name?.[0]}</AvatarFallback>
                    </Avatar>
                    <div>
                      <p className="font-medium">{entry.name} {entry.is_self && <span className="text-xs text-muted-foreground">(vous)</span>}</p>
                      <p className="text-xs text-muted-foreground">{entry.badges_count} badges</p>
                    </div>
                  </div>
                  <p className="font-bold text-primary">{entry.total_points} pts</p>
                </div>
              ))}
            </CardContent>
          </Card>
        </TabsContent>

        {/* Groups Tab */}
        <TabsContent value="groups" className="p-4 space-y-4">
          <p className="text-sm text-muted-foreground mb-2">Rejoignez des communautés pour partager vos objectifs !</p>
          {groups.map(group => (
            <Card key={group.group_id}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="font-medium">{group.name}</p>
                    <p className="text-sm text-muted-foreground">{group.description}</p>
                    <p className="text-xs text-muted-foreground mt-1">{group.member_count} membres</p>
                  </div>
                  <Button variant={group.is_member ? 'outline' : 'default'} size="sm" onClick={() => toggleGroup(group.group_id, group.is_member)}>
                    {group.is_member ? 'Quitter' : 'Rejoindre'}
                  </Button>
                </div>
              </CardContent>
            </Card>
          ))}
        </TabsContent>

        {/* Notifications Tab */}
        <TabsContent value="notifications" className="p-4 space-y-2">
          {notifications.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <Bell className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Aucune notification</p>
              </CardContent>
            </Card>
          ) : (
            notifications.map(notif => (
              <Card key={notif.notification_id} className={!notif.read ? 'border-primary/50 bg-primary/5' : ''}>
                <CardContent className="p-4">
                  <div className="flex items-start gap-3">
                    {notif.from_user_picture && (
                      <Avatar className="w-8 h-8">
                        <AvatarImage src={notif.from_user_picture} />
                        <AvatarFallback>{notif.from_user_name?.[0]}</AvatarFallback>
                      </Avatar>
                    )}
                    <div className="flex-1">
                      <p className="text-sm">{notif.content}</p>
                      <p className="text-xs text-muted-foreground mt-1">{new Date(notif.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))
          )}
        </TabsContent>
      </Tabs>

      {/* Post Dialog */}
      <Dialog open={showPostDialog} onOpenChange={setShowPostDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nouvelle publication</DialogTitle>
          </DialogHeader>
          <Textarea placeholder="Partagez quelque chose..." value={newPost} onChange={(e) => setNewPost(e.target.value)} rows={4} />
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowPostDialog(false)}>Annuler</Button>
            <Button onClick={createPost} disabled={!newPost.trim()}>Publier</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Message Dialog */}
      <Dialog open={showMessageDialog} onOpenChange={setShowMessageDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <Avatar className="w-8 h-8">
                <AvatarImage src={selectedConversation?.partner_picture} />
                <AvatarFallback>{selectedConversation?.partner_name?.[0]}</AvatarFallback>
              </Avatar>
              {selectedConversation?.partner_name}
            </DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-[300px] pr-4">
            <div className="space-y-3">
              {messages.map(msg => (
                <div key={msg.message_id} className={`flex ${msg.sender_id === user?.user_id ? 'justify-end' : 'justify-start'}`}>
                  <div className={`max-w-[80%] p-3 rounded-lg ${msg.sender_id === user?.user_id ? 'bg-primary text-primary-foreground' : 'bg-muted'}`}>
                    <p className="text-sm">{msg.content}</p>
                    <p className="text-[10px] opacity-70 mt-1">{new Date(msg.created_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}</p>
                  </div>
                </div>
              ))}
            </div>
          </ScrollArea>
          <div className="flex gap-2 mt-4">
            <Input placeholder="Votre message..." value={newMessage} onChange={(e) => setNewMessage(e.target.value)} onKeyDown={(e) => e.key === 'Enter' && sendMessage()} />
            <Button onClick={sendMessage} disabled={!newMessage.trim()}>
              <Send className="w-4 h-4" />
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      {/* Profile Dialog */}
      <Dialog open={showProfileDialog} onOpenChange={setShowProfileDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Profil</DialogTitle>
          </DialogHeader>
          {selectedProfile && (
            <div className="space-y-4">
              <div className="flex items-center gap-4">
                <Avatar className="w-16 h-16">
                  <AvatarImage src={selectedProfile.picture} />
                  <AvatarFallback className="text-xl">{selectedProfile.name?.[0]}</AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-bold text-lg">{selectedProfile.name}</p>
                  <p className="text-sm text-muted-foreground">{selectedProfile.total_points} points • {selectedProfile.badges_count} badges</p>
                </div>
              </div>
              <div className="flex gap-2 flex-wrap">
                {selectedProfile.badges?.slice(0, 6).map(b => (
                  <Badge key={b.badge_id} variant="secondary">{b.badge_name}</Badge>
                ))}
              </div>
              {!selectedProfile.is_self && (
                <div className="flex gap-2">
                  {selectedProfile.is_friend ? (
                    <>
                      <Button className="flex-1" onClick={() => { openConversation(selectedProfile.user_id, selectedProfile.name, selectedProfile.picture); setShowProfileDialog(false); }}>
                        <MessageCircle className="w-4 h-4 mr-2" /> Message
                      </Button>
                      <Button variant="outline" onClick={() => { setChallengeFriend(selectedProfile); setShowChallengeDialog(true); setShowProfileDialog(false); }}>
                        <Swords className="w-4 h-4" />
                      </Button>
                    </>
                  ) : selectedProfile.is_pending ? (
                    <Button disabled className="flex-1">En attente...</Button>
                  ) : (
                    <Button className="flex-1" onClick={() => { sendFriendRequest(selectedProfile.user_id); setShowProfileDialog(false); }}>
                      <UserPlus className="w-4 h-4 mr-2" /> Ajouter en ami
                    </Button>
                  )}
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

      {/* Challenge Dialog */}
      <Dialog open={showChallengeDialog} onOpenChange={setShowChallengeDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Lancer un défi</DialogTitle>
            <DialogDescription>Défiez {challengeFriend?.name} !</DialogDescription>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm font-medium">Type de défi</label>
              <select className="w-full mt-1 p-2 border rounded-md" value={challengeConfig.type} onChange={(e) => setChallengeConfig({ ...challengeConfig, type: e.target.value })}>
                <option value="steps">🚶 Pas</option>
                <option value="meals">🍽️ Repas enregistrés</option>
                <option value="workouts">💪 Entraînements</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium">Objectif</label>
              <Input type="number" value={challengeConfig.target} onChange={(e) => setChallengeConfig({ ...challengeConfig, target: parseInt(e.target.value) || 0 })} />
            </div>
            <div>
              <label className="text-sm font-medium">Durée (jours)</label>
              <Input type="number" value={challengeConfig.duration_days} onChange={(e) => setChallengeConfig({ ...challengeConfig, duration_days: parseInt(e.target.value) || 7 })} />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowChallengeDialog(false)}>Annuler</Button>
            <Button onClick={createChallenge}>Lancer le défi !</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
