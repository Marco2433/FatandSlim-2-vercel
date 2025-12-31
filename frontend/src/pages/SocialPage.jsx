import { useState, useEffect, useCallback, useRef } from 'react';
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
  ChevronRight,
  MessageSquare,
  Upload,
  Globe,
  Users2,
  Target,
  Sparkles,
  ChevronDown
} from 'lucide-react';

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Post Card Component (moved outside to avoid nested component issue)
const PostCard = ({ post, showGroupBadge = false, groups, onLike, onComment, onViewProfile }) => (
  <Card key={post.post_id}>
    <CardContent className="p-4">
      <div className="flex items-start gap-3">
        <Avatar className="w-10 h-10 cursor-pointer" onClick={() => onViewProfile(post.user_id)}>
          <AvatarImage src={post.user_picture} />
          <AvatarFallback>{post.user_name?.[0]}</AvatarFallback>
        </Avatar>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <p className="font-medium text-sm">{post.user_name}</p>
            {showGroupBadge && post.group_id && (
              <Badge variant="secondary" className="text-xs">
                {groups.find(g => g.group_id === post.group_id)?.name || post.group_id}
              </Badge>
            )}
          </div>
          <p className="text-xs text-muted-foreground">
            {new Date(post.created_at).toLocaleDateString('fr-FR', { day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit' })}
          </p>
          
          <p className="mt-2 whitespace-pre-wrap">{post.content}</p>
          
          {/* Image */}
          {(post.image_url || post.image_base64) && (
            <img 
              src={post.image_url || post.image_base64} 
              alt="Post" 
              className="mt-3 rounded-lg max-h-64 w-full object-cover"
            />
          )}
          
          {/* Shared Item */}
          {post.shared_item && post.type === 'share_recipe' && (
            <div className="mt-3 p-3 bg-muted/50 rounded-lg border">
              <p className="font-medium text-sm">🍳 {post.shared_item.name}</p>
              <p className="text-xs text-muted-foreground">
                {post.shared_item.calories} kcal • {post.shared_item.prep_time}
              </p>
            </div>
          )}
          
          {post.shared_item && post.type === 'share_program' && (
            <div className="mt-3 p-3 bg-muted/50 rounded-lg border">
              <p className="font-medium text-sm">💪 {post.shared_item.name}</p>
              <p className="text-xs text-muted-foreground">{post.shared_item.description}</p>
            </div>
          )}
          
          {/* Actions */}
          <div className="flex items-center gap-4 mt-3">
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => onLike(post.post_id)} 
              className={post.user_liked ? 'text-red-500' : ''}
            >
              <Heart className={`w-4 h-4 mr-1 ${post.user_liked ? 'fill-current' : ''}`} />
              {post.likes_count || 0}
            </Button>
            <Button 
              variant="ghost" 
              size="sm" 
              onClick={() => onComment(post)}
            >
              <MessageSquare className="w-4 h-4 mr-1" />
              {post.comments_count || 0}
            </Button>
          </div>
        </div>
      </div>
    </CardContent>
  </Card>
);

export default function SocialPage() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('feed');
  const [loading, setLoading] = useState(true);
  const fileInputRef = useRef(null);
  
  // Data states
  const [publicFeed, setPublicFeed] = useState([]);
  const [friends, setFriends] = useState([]);
  const [friendRequests, setFriendRequests] = useState({ received: [], sent: [] });
  const [conversations, setConversations] = useState([]);
  const [notifications, setNotifications] = useState([]);
  const [groups, setGroups] = useState([]);
  const [challenges, setChallenges] = useState([]);
  
  // Leaderboard states
  const [leaderboard, setLeaderboard] = useState([]);
  const [leaderboardType, setLeaderboardType] = useState('friends');
  const [selectedGroupForLeaderboard, setSelectedGroupForLeaderboard] = useState(null);
  
  // Group feed states
  const [selectedGroup, setSelectedGroup] = useState(null);
  const [groupFeed, setGroupFeed] = useState([]);
  const [groupChallenge, setGroupChallenge] = useState(null);
  const [showGroupFeed, setShowGroupFeed] = useState(false);
  
  // Search
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  
  // Post creation
  const [showPostDialog, setShowPostDialog] = useState(false);
  const [newPost, setNewPost] = useState('');
  const [postImage, setPostImage] = useState(null);
  const [postImagePreview, setPostImagePreview] = useState(null);
  const [postingToGroup, setPostingToGroup] = useState(null);
  const [creatingPost, setCreatingPost] = useState(false);
  
  // Comments
  const [showCommentsDialog, setShowCommentsDialog] = useState(false);
  const [selectedPostForComments, setSelectedPostForComments] = useState(null);
  const [comments, setComments] = useState([]);
  const [newComment, setNewComment] = useState('');
  const [loadingComments, setLoadingComments] = useState(false);
  
  // Messages
  const [showMessageDialog, setShowMessageDialog] = useState(false);
  const [selectedConversation, setSelectedConversation] = useState(null);
  const [messages, setMessages] = useState([]);
  const [newMessage, setNewMessage] = useState('');
  
  // Profile
  const [showProfileDialog, setShowProfileDialog] = useState(false);
  const [selectedProfile, setSelectedProfile] = useState(null);
  
  // Challenges
  const [showChallengeDialog, setShowChallengeDialog] = useState(false);
  const [challengeConfig, setChallengeConfig] = useState({ type: 'steps', target: 10000, duration_days: 7 });
  const [challengeFriend, setChallengeFriend] = useState(null);

  // Fetch all data
  const fetchData = useCallback(async () => {
    setLoading(true);
    try {
      const [publicFeedRes, friendsRes, requestsRes, convsRes, notifsRes, groupsRes, challengesRes] = await Promise.allSettled([
        axios.get(`${API}/social/feed/public`, { withCredentials: true }),
        axios.get(`${API}/social/friends`, { withCredentials: true }),
        axios.get(`${API}/social/friends/requests`, { withCredentials: true }),
        axios.get(`${API}/social/messages`, { withCredentials: true }),
        axios.get(`${API}/social/notifications`, { withCredentials: true }),
        axios.get(`${API}/social/groups`, { withCredentials: true }),
        axios.get(`${API}/social/challenges`, { withCredentials: true })
      ]);
      
      if (publicFeedRes.status === 'fulfilled') setPublicFeed(publicFeedRes.value.data.posts || []);
      if (friendsRes.status === 'fulfilled') setFriends(friendsRes.value.data.friends || []);
      if (requestsRes.status === 'fulfilled') setFriendRequests(requestsRes.value.data);
      if (convsRes.status === 'fulfilled') setConversations(convsRes.value.data.conversations || []);
      if (notifsRes.status === 'fulfilled') setNotifications(notifsRes.value.data.notifications || []);
      if (groupsRes.status === 'fulfilled') setGroups(groupsRes.value.data.groups || []);
      if (challengesRes.status === 'fulfilled') setChallenges(challengesRes.value.data.challenges || []);
      
      // Fetch default leaderboard
      fetchLeaderboard('friends');
    } catch (error) {
      console.error('Error fetching social data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Fetch leaderboard
  const fetchLeaderboard = async (type, groupId = null) => {
    try {
      let url = `${API}/social/leaderboard/${type}`;
      if (type === 'group' && groupId) {
        url += `?group_id=${groupId}`;
      }
      const response = await axios.get(url, { withCredentials: true });
      setLeaderboard(response.data.leaderboard || []);
      setLeaderboardType(type);
    } catch (error) {
      console.error('Error fetching leaderboard:', error);
      // Fallback to friends leaderboard
      if (type !== 'friends') {
        fetchLeaderboard('friends');
      }
    }
  };

  // Fetch group feed
  const fetchGroupFeed = async (groupId) => {
    try {
      const [feedRes, challengeRes] = await Promise.allSettled([
        axios.get(`${API}/social/groups/${groupId}/feed`, { withCredentials: true }),
        axios.get(`${API}/social/groups/${groupId}/challenge`, { withCredentials: true })
      ]);
      
      if (feedRes.status === 'fulfilled') setGroupFeed(feedRes.value.data.posts || []);
      if (challengeRes.status === 'fulfilled') setGroupChallenge(challengeRes.value.data);
    } catch (error) {
      console.error('Error fetching group feed:', error);
    }
  };

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
  const handleImageSelect = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        toast.error('Image trop grande (max 5MB)');
        return;
      }
      setPostImage(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setPostImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const createPost = async () => {
    if (!newPost.trim() && !postImagePreview) return;
    setCreatingPost(true);
    
    try {
      const postData = {
        content: newPost.trim(),
        type: postImagePreview ? 'image' : 'text',
        image_base64: postImagePreview,
        group_id: postingToGroup,
        is_public: !postingToGroup
      };
      
      await axios.post(`${API}/social/post`, postData, { withCredentials: true });
      
      setNewPost('');
      setPostImage(null);
      setPostImagePreview(null);
      setPostingToGroup(null);
      setShowPostDialog(false);
      toast.success('Publié !');
      
      // Refresh feed
      if (postingToGroup && selectedGroup) {
        fetchGroupFeed(postingToGroup);
      } else {
        const response = await axios.get(`${API}/social/feed/public`, { withCredentials: true });
        setPublicFeed(response.data.posts || []);
      }
    } catch (error) {
      toast.error('Erreur lors de la publication');
    } finally {
      setCreatingPost(false);
    }
  };

  const likePost = async (postId) => {
    try {
      await axios.post(`${API}/social/post/${postId}/like`, {}, { withCredentials: true });
      
      // Update local state
      setPublicFeed(prev => prev.map(p => {
        if (p.post_id === postId) {
          return {
            ...p,
            user_liked: !p.user_liked,
            likes_count: p.user_liked ? (p.likes_count || 1) - 1 : (p.likes_count || 0) + 1
          };
        }
        return p;
      }));
      
      setGroupFeed(prev => prev.map(p => {
        if (p.post_id === postId) {
          return {
            ...p,
            user_liked: !p.user_liked,
            likes_count: p.user_liked ? (p.likes_count || 1) - 1 : (p.likes_count || 0) + 1
          };
        }
        return p;
      }));
    } catch (error) {
      toast.error('Erreur');
    }
  };

  // Comments
  const openComments = async (post) => {
    setSelectedPostForComments(post);
    setShowCommentsDialog(true);
    setLoadingComments(true);
    
    try {
      const response = await axios.get(`${API}/social/post/${post.post_id}/comments`, { withCredentials: true });
      setComments(response.data.comments || []);
    } catch (error) {
      console.error('Error loading comments:', error);
    } finally {
      setLoadingComments(false);
    }
  };

  const addComment = async () => {
    if (!newComment.trim() || !selectedPostForComments) return;
    
    try {
      await axios.post(`${API}/social/post/${selectedPostForComments.post_id}/comment`, {
        content: newComment.trim()
      }, { withCredentials: true });
      
      setNewComment('');
      
      // Refresh comments
      const response = await axios.get(`${API}/social/post/${selectedPostForComments.post_id}/comments`, { withCredentials: true });
      setComments(response.data.comments || []);
      
      // Update comment count
      setPublicFeed(prev => prev.map(p => {
        if (p.post_id === selectedPostForComments.post_id) {
          return { ...p, comments_count: (p.comments_count || 0) + 1 };
        }
        return p;
      }));
      
      setGroupFeed(prev => prev.map(p => {
        if (p.post_id === selectedPostForComments.post_id) {
          return { ...p, comments_count: (p.comments_count || 0) + 1 };
        }
        return p;
      }));
      
      toast.success('Commentaire ajouté');
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

  const openGroupFeed = (group) => {
    if (!group.is_member) {
      toast.error('Rejoignez le groupe pour voir son fil');
      return;
    }
    setSelectedGroup(group);
    setShowGroupFeed(true);
    fetchGroupFeed(group.group_id);
  };

  // Group Challenges
  const acceptGroupChallenge = async (groupId) => {
    try {
      await axios.post(`${API}/social/groups/${groupId}/challenge/accept`, {}, { withCredentials: true });
      toast.success('Défi accepté !');
      fetchGroupFeed(groupId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur');
    }
  };

  const completeGroupChallenge = async (groupId) => {
    try {
      const response = await axios.post(`${API}/social/groups/${groupId}/challenge/complete`, {}, { withCredentials: true });
      toast.success(response.data.message);
      fetchGroupFeed(groupId);
    } catch (error) {
      toast.error(error.response?.data?.detail || 'Erreur');
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

  // Helper function to render posts with PostCard component
  const renderPostCard = (post, showGroupBadge = false) => (
    <PostCard 
      key={post.post_id} 
      post={post} 
      showGroupBadge={showGroupBadge}
      groups={groups}
      onLike={likePost}
      onComment={openComments}
      onViewProfile={viewProfile}
    />
  );

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
            <Button variant="ghost" size="icon" onClick={() => showGroupFeed ? setShowGroupFeed(false) : navigate('/dashboard')}>
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <div>
              <h1 className="text-lg font-bold">
                {showGroupFeed && selectedGroup ? selectedGroup.name : 'Communauté'}
              </h1>
              <p className="text-xs text-muted-foreground">
                {showGroupFeed ? `${selectedGroup?.member_count || 0} membres` : `${friends.length} amis`}
              </p>
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

      {/* Group Feed View */}
      {showGroupFeed && selectedGroup ? (
        <div className="p-4 space-y-4">
          {/* Group Challenge */}
          {groupChallenge?.challenge && (
            <Card className="border-primary/50 bg-gradient-to-r from-primary/10 to-secondary/10">
              <CardContent className="p-4">
                <div className="flex items-center justify-between mb-2">
                  <h3 className="font-semibold flex items-center gap-2">
                    <Target className="w-5 h-5 text-primary" />
                    Défi du jour
                  </h3>
                  <Badge>{groupChallenge.challenge.points} pts</Badge>
                </div>
                <p className="text-sm mb-3">{groupChallenge.challenge.description}</p>
                <div className="flex items-center justify-between text-xs text-muted-foreground mb-3">
                  <span>{groupChallenge.participants_count || 0} participants</span>
                  <span>{groupChallenge.completions_count || 0} complétés</span>
                </div>
                {!groupChallenge.participation ? (
                  <Button size="sm" onClick={() => acceptGroupChallenge(selectedGroup.group_id)}>
                    Accepter le défi
                  </Button>
                ) : groupChallenge.participation.completed ? (
                  <Badge variant="secondary" className="bg-green-500/20 text-green-600">
                    <Check className="w-3 h-3 mr-1" /> Complété !
                  </Badge>
                ) : (
                  <Button size="sm" onClick={() => completeGroupChallenge(selectedGroup.group_id)}>
                    <Check className="w-4 h-4 mr-1" /> Marquer comme fait
                  </Button>
                )}
              </CardContent>
            </Card>
          )}

          {/* Post to Group Button */}
          <Button className="w-full" onClick={() => { setPostingToGroup(selectedGroup.group_id); setShowPostDialog(true); }}>
            <Plus className="w-4 h-4 mr-2" /> Publier dans ce groupe
          </Button>

          {/* Group Feed */}
          {groupFeed.length === 0 ? (
            <Card>
              <CardContent className="p-8 text-center">
                <Users className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                <p className="text-muted-foreground">Aucune publication dans ce groupe</p>
                <p className="text-sm text-muted-foreground mt-1">Soyez le premier à partager !</p>
              </CardContent>
            </Card>
          ) : (
            <div className="space-y-4">
              {groupFeed.map(post => renderPostCard(post))}
            </div>
          )}
        </div>
      ) : (
        /* Main Tabs */
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

          {/* Public Feed Tab */}
          <TabsContent value="feed" className="p-4 space-y-4">
            {/* Post Button */}
            <Button className="w-full" onClick={() => { setPostingToGroup(null); setShowPostDialog(true); }}>
              <Plus className="w-4 h-4 mr-2" /> Publier quelque chose
            </Button>

            {/* Friend Requests Alert */}
            {friendRequests.received?.length > 0 && (
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

            {/* Public Feed */}
            <div className="flex items-center gap-2 mb-2">
              <Globe className="w-4 h-4 text-muted-foreground" />
              <span className="text-sm font-medium">Fil public de la communauté</span>
            </div>
            
            {publicFeed.length === 0 ? (
              <Card>
                <CardContent className="p-8 text-center">
                  <Users className="w-12 h-12 mx-auto text-muted-foreground mb-4" />
                  <p className="text-muted-foreground">Aucune publication pour le moment</p>
                  <p className="text-sm text-muted-foreground mt-1">Soyez le premier à partager !</p>
                </CardContent>
              </Card>
            ) : (
              <div className="space-y-4">
                {publicFeed.map(post => renderPostCard(post, true))}
              </div>
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
                        <span>{u.name}</span>
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
            {/* Leaderboard Type Selector */}
            <div className="flex gap-2 flex-wrap">
              <Button 
                size="sm" 
                variant={leaderboardType === 'friends' ? 'default' : 'outline'}
                onClick={() => fetchLeaderboard('friends')}
              >
                <Users className="w-4 h-4 mr-1" /> Amis
              </Button>
              <Button 
                size="sm" 
                variant={leaderboardType === 'global' ? 'default' : 'outline'}
                onClick={() => fetchLeaderboard('global')}
              >
                <Globe className="w-4 h-4 mr-1" /> Global
              </Button>
              {groups.filter(g => g.is_member).map(group => (
                <Button 
                  key={group.group_id}
                  size="sm" 
                  variant={leaderboardType === 'group' && selectedGroupForLeaderboard === group.group_id ? 'default' : 'outline'}
                  onClick={() => { setSelectedGroupForLeaderboard(group.group_id); fetchLeaderboard('group', group.group_id); }}
                >
                  {group.name}
                </Button>
              ))}
            </div>

            <Card>
              <CardHeader className="py-3 px-4">
                <CardTitle className="text-sm flex items-center gap-2">
                  <Trophy className="w-5 h-5 text-yellow-500" /> 
                  Classement {leaderboardType === 'friends' ? 'Amis' : leaderboardType === 'global' ? 'Global' : 'Groupe'}
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                {leaderboard.length === 0 ? (
                  <p className="p-4 text-center text-muted-foreground">Aucun classement disponible</p>
                ) : (
                  leaderboard.map((entry, index) => (
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
                  ))
                )}
              </CardContent>
            </Card>
          </TabsContent>

          {/* Groups Tab */}
          <TabsContent value="groups" className="p-4 space-y-4">
            <p className="text-sm text-muted-foreground mb-2">Rejoignez des communautés thématiques pour partager vos objectifs !</p>
            {groups.map(group => (
              <Card key={group.group_id} className={group.is_member ? 'border-primary/30' : ''}>
                <CardContent className="p-4">
                  <div className="flex items-center justify-between">
                    <div className="flex-1 cursor-pointer" onClick={() => openGroupFeed(group)}>
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{group.name}</p>
                        {group.is_member && <Badge variant="secondary" className="text-xs">Membre</Badge>}
                      </div>
                      <p className="text-sm text-muted-foreground">{group.description}</p>
                      <p className="text-xs text-muted-foreground mt-1">{group.member_count} membres</p>
                    </div>
                    <div className="flex flex-col gap-2">
                      <Button 
                        variant={group.is_member ? 'outline' : 'default'} 
                        size="sm" 
                        onClick={(e) => { e.stopPropagation(); toggleGroup(group.group_id, group.is_member); }}
                      >
                        {group.is_member ? 'Quitter' : 'Rejoindre'}
                      </Button>
                      {group.is_member && (
                        <Button 
                          variant="ghost" 
                          size="sm"
                          onClick={() => openGroupFeed(group)}
                        >
                          Voir le fil <ChevronRight className="w-4 h-4 ml-1" />
                        </Button>
                      )}
                    </div>
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
      )}

      {/* Post Dialog */}
      <Dialog open={showPostDialog} onOpenChange={setShowPostDialog}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>
              {postingToGroup ? `Publier dans ${groups.find(g => g.group_id === postingToGroup)?.name || 'le groupe'}` : 'Nouvelle publication'}
            </DialogTitle>
          </DialogHeader>
          <Textarea 
            placeholder="Partagez quelque chose..." 
            value={newPost} 
            onChange={(e) => setNewPost(e.target.value)} 
            rows={4} 
          />
          
          {/* Image Preview */}
          {postImagePreview && (
            <div className="relative">
              <img src={postImagePreview} alt="Preview" className="w-full h-48 object-cover rounded-lg" />
              <Button 
                variant="destructive" 
                size="icon" 
                className="absolute top-2 right-2"
                onClick={() => { setPostImage(null); setPostImagePreview(null); }}
              >
                <X className="w-4 h-4" />
              </Button>
            </div>
          )}
          
          <div className="flex gap-2">
            <input
              type="file"
              accept="image/*"
              ref={fileInputRef}
              onChange={handleImageSelect}
              className="hidden"
            />
            <Button variant="outline" size="sm" onClick={() => fileInputRef.current?.click()}>
              <ImageIcon className="w-4 h-4 mr-2" />
              Photo
            </Button>
          </div>
          
          <DialogFooter>
            <Button variant="outline" onClick={() => { setShowPostDialog(false); setPostImage(null); setPostImagePreview(null); }}>Annuler</Button>
            <Button onClick={createPost} disabled={creatingPost || (!newPost.trim() && !postImagePreview)}>
              {creatingPost ? <Loader2 className="w-4 h-4 animate-spin mr-2" /> : null}
              Publier
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Comments Dialog */}
      <Dialog open={showCommentsDialog} onOpenChange={setShowCommentsDialog}>
        <DialogContent className="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Commentaires</DialogTitle>
          </DialogHeader>
          <ScrollArea className="h-[300px] pr-4">
            {loadingComments ? (
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-6 h-6 animate-spin" />
              </div>
            ) : comments.length === 0 ? (
              <p className="text-center text-muted-foreground py-8">Aucun commentaire</p>
            ) : (
              <div className="space-y-3">
                {comments.map(comment => (
                  <div key={comment.comment_id} className="flex gap-3">
                    <Avatar className="w-8 h-8">
                      <AvatarImage src={comment.user_picture} />
                      <AvatarFallback>{comment.user_name?.[0]}</AvatarFallback>
                    </Avatar>
                    <div className="flex-1 bg-muted p-3 rounded-lg">
                      <p className="font-medium text-sm">{comment.user_name}</p>
                      <p className="text-sm">{comment.content}</p>
                      <p className="text-[10px] text-muted-foreground mt-1">
                        {new Date(comment.created_at).toLocaleTimeString('fr-FR', { hour: '2-digit', minute: '2-digit' })}
                      </p>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </ScrollArea>
          <div className="flex gap-2 mt-4">
            <Input 
              placeholder="Écrire un commentaire..." 
              value={newComment} 
              onChange={(e) => setNewComment(e.target.value)} 
              onKeyDown={(e) => e.key === 'Enter' && addComment()} 
            />
            <Button onClick={addComment} disabled={!newComment.trim()}>
              <Send className="w-4 h-4" />
            </Button>
          </div>
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
