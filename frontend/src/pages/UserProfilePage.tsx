import React, { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useParams, Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import {
  User,
  Award,
  Calendar,
  Mail,
  Edit3,
  BookOpen,
  Star,
  CheckCircle,
  Clock
} from 'lucide-react';
import { Button } from '../components/ui/button';
import { Card, CardHeader, CardTitle, CardContent } from '../components/ui/card';
import { AuroraBackground } from '../components/ui/aurora-background';
import { useAuth } from '../context/AuthContext';
import { formatDate } from '../i18n/config';

interface Contribution {
  id: string;
  type: 'correction' | 'addition' | 'removal';
  targetLabel: string;
  status: 'pending' | 'approved' | 'rejected';
  date: string;
  description: string;
}

interface UserProfile {
  username: string;
  email: string;
  joinDate: string;
  contributions: Contribution[];
  badges: string[];
  researchInterests: string[];
  bio: string;
}

const UserProfilePage: React.FC = () => {
  const { t, i18n } = useTranslation();
  const { userId } = useParams<{ userId?: string }>();
  const { user: authUser, isAuthenticated } = useAuth();
  const [isEditing, setIsEditing] = useState(false);

  // For now, use mock data (in real implementation, fetch from API)
  const [profile] = useState<UserProfile>({
    username: authUser?.username || 'Scholar',
    email: authUser?.email || 'scholar@university.edu',
    joinDate: '2025-01-01',
    contributions: [
      {
        id: '1',
        type: 'correction',
        targetLabel: 'Stoic Determinism',
        status: 'approved',
        date: '2025-10-15',
        description: 'Corrected citation for Chrysippus fragment'
      },
      {
        id: '2',
        type: 'addition',
        targetLabel: 'Aristotle on Chance',
        status: 'pending',
        date: '2025-11-10',
        description: 'Added missing reference to Physics II.4-6'
      },
      {
        id: '3',
        type: 'correction',
        targetLabel: 'Epicurean Clinamen',
        status: 'approved',
        date: '2025-09-20',
        description: 'Updated Greek terminology with proper diacritics'
      }
    ],
    badges: ['bronze'],
    researchInterests: ['Stoic Philosophy', 'Hellenistic Ethics', 'Ancient Greek'],
    bio: 'PhD candidate researching ancient philosophical debates on moral responsibility and determinism.'
  });

  const [editedProfile, setEditedProfile] = useState(profile);

  const isOwnProfile = !userId || (authUser && userId === authUser.username);

  const getBadgeInfo = (badge: string) => {
    switch (badge) {
      case 'bronze':
        return { color: 'bg-orange-100 text-orange-700 border-orange-200', label: t('community.badges.bronze'), icon: '🥉' };
      case 'silver':
        return { color: 'bg-gray-100 text-gray-700 border-gray-200', label: t('community.badges.silver'), icon: '🥈' };
      case 'gold':
        return { color: 'bg-yellow-100 text-yellow-700 border-yellow-200', label: t('community.badges.gold'), icon: '🥇' };
      default:
        return { color: 'bg-gray-100 text-gray-700', label: badge, icon: '🏅' };
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'approved':
        return <CheckCircle className="w-4 h-4 text-green-500" />;
      case 'pending':
        return <Clock className="w-4 h-4 text-yellow-500" />;
      case 'rejected':
        return <Star className="w-4 h-4 text-red-500" />;
      default:
        return null;
    }
  };

  const handleSaveProfile = () => {
    // In real implementation, save to API
    console.log('Saving profile:', editedProfile);
    setIsEditing(false);
  };

  if (!isAuthenticated && isOwnProfile) {
    return (
      <AuroraBackground className="!min-h-screen !h-auto py-12">
        <div className="text-center py-12 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
          <User className="w-16 h-16 text-academic-muted mx-auto mb-4" />
          <h2 className="text-xl font-semibold mb-2">{t('community.authRequired')}</h2>
          <p className="text-academic-muted mb-4">{t('community.authRequiredDesc')}</p>
          <Link to="/login">
            <Button>{t('nav.login')}</Button>
          </Link>
        </div>
      </AuroraBackground>
    );
  }

  return (
    <AuroraBackground className="!min-h-screen !h-auto py-12">
      <div className="space-y-6 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative z-10">
      {/* Profile Header */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-4">
              <div className="w-20 h-20 bg-primary-100 rounded-full flex items-center justify-center">
                <User className="w-10 h-10 text-primary-600" />
              </div>
              <div>
                {isEditing ? (
                  <input
                    type="text"
                    value={editedProfile.username}
                    onChange={(e) => setEditedProfile(prev => ({ ...prev, username: e.target.value }))}
                    className="text-2xl font-bold border-b border-primary-600 focus:outline-none"
                  />
                ) : (
                  <h1 className="text-2xl font-bold text-academic-text">{profile.username}</h1>
                )}
                <div className="flex items-center gap-2 text-academic-muted mt-1">
                  <Mail className="w-4 h-4" />
                  <span>{profile.email}</span>
                </div>
                <div className="flex items-center gap-2 text-academic-muted mt-1">
                  <Calendar className="w-4 h-4" />
                  <span>{t('community.profile.joinDate')}: {formatDate(profile.joinDate, i18n.language)}</span>
                </div>
              </div>
            </div>

            {isOwnProfile && (
              <Button
                variant="outline"
                onClick={() => isEditing ? handleSaveProfile() : setIsEditing(true)}
                className="flex items-center gap-2"
              >
                <Edit3 className="w-4 h-4" />
                {isEditing ? t('common.save') : t('common.edit')}
              </Button>
            )}
          </div>

          {/* Bio */}
          <div className="mt-4">
            {isEditing ? (
              <textarea
                value={editedProfile.bio}
                onChange={(e) => setEditedProfile(prev => ({ ...prev, bio: e.target.value }))}
                rows={3}
                className="w-full p-3 border rounded-lg focus:ring-2 focus:ring-primary-500"
                placeholder="Tell us about your research..."
              />
            ) : (
              <p className="text-academic-muted">{profile.bio}</p>
            )}
          </div>

          {/* Badges */}
          <div className="mt-4">
            <h3 className="text-sm font-semibold text-academic-muted uppercase tracking-wider mb-2">
              {t('community.badgesTitle')}
            </h3>
            <div className="flex flex-wrap gap-2">
              {profile.badges.map(badge => {
                const info = getBadgeInfo(badge);
                return (
                  <span
                    key={badge}
                    className={`px-3 py-1 rounded-full border text-sm font-medium flex items-center gap-2 ${info.color}`}
                  >
                    <span>{info.icon}</span>
                    {info.label}
                  </span>
                );
              })}
            </div>
          </div>

          {/* Research Interests */}
          <div className="mt-4">
            <h3 className="text-sm font-semibold text-academic-muted uppercase tracking-wider mb-2">
              {t('community.profile.researchInterests')}
            </h3>
            <div className="flex flex-wrap gap-2">
              {profile.researchInterests.map(interest => (
                <span
                  key={interest}
                  className="px-3 py-1 bg-primary-50 text-primary-700 rounded-full text-sm"
                >
                  {interest}
                </span>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card>
          <CardContent className="p-4 text-center">
            <BookOpen className="w-8 h-8 text-blue-500 mx-auto mb-2" />
            <p className="text-2xl font-bold">{profile.contributions.length}</p>
            <p className="text-sm text-academic-muted">{t('community.totalContributions')}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <CheckCircle className="w-8 h-8 text-green-500 mx-auto mb-2" />
            <p className="text-2xl font-bold">
              {profile.contributions.filter(c => c.status === 'approved').length}
            </p>
            <p className="text-sm text-academic-muted">{t('community.approved')}</p>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4 text-center">
            <Clock className="w-8 h-8 text-yellow-500 mx-auto mb-2" />
            <p className="text-2xl font-bold">
              {profile.contributions.filter(c => c.status === 'pending').length}
            </p>
            <p className="text-sm text-academic-muted">{t('community.pendingReviewShort')}</p>
          </CardContent>
        </Card>
      </div>

      {/* Contributions List */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Award className="w-5 h-5" />
            {t('community.profile.contributions')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          {profile.contributions.length === 0 ? (
            <div className="text-center py-8">
              <BookOpen className="w-12 h-12 text-academic-muted mx-auto mb-3" />
              <p className="text-academic-muted">{t('community.noContributions')}</p>
              <Link to="/community/contribute" className="mt-4 inline-block">
                <Button variant="outline">{t('community.makeFirst')}</Button>
              </Link>
            </div>
          ) : (
            <div className="space-y-4">
              {profile.contributions.map((contribution) => (
                <motion.div
                  key={contribution.id}
                  initial={{ opacity: 0, x: -20 }}
                  animate={{ opacity: 1, x: 0 }}
                  className="p-4 border rounded-lg hover:bg-gray-50 transition-colors"
                >
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(contribution.status)}
                      <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                        contribution.type === 'correction' ? 'bg-blue-100 text-blue-700' :
                        contribution.type === 'addition' ? 'bg-green-100 text-green-700' :
                        'bg-red-100 text-red-700'
                      }`}>
                        {contribution.type}
                      </span>
                      <span className="font-medium">{contribution.targetLabel}</span>
                    </div>
                    <span className="text-sm text-academic-muted">
                      {formatDate(contribution.date, i18n.language)}
                    </span>
                  </div>
                  <p className="text-sm text-academic-muted">{contribution.description}</p>
                </motion.div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>

      {/* Newsletter Signup */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Mail className="w-5 h-5" />
            {t('community.newsletter.title')}
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-academic-muted mb-4">
            {t('community.newsletter.description')}
          </p>
          <div className="flex gap-2">
            <input
              type="email"
              placeholder={t('community.newsletter.emailPlaceholder')}
              className="flex-1 p-3 border rounded-lg focus:ring-2 focus:ring-primary-500"
              defaultValue={profile.email}
            />
            <Button>
              {t('community.newsletter.subscribe')}
            </Button>
          </div>
        </CardContent>
      </Card>
      </div>
    </AuroraBackground>
  );
};

export default UserProfilePage;
