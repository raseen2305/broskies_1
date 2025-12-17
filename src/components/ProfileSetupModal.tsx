import React, { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { X, User, Building2, Globe, MapPin, Map, Github } from "lucide-react";
import { profileAPI } from "../services/profileAPI";
import { ProfileSetupRequest, UserProfile } from "../types";

export interface ProfileSetupModalProps {
  isOpen: boolean;
  onClose: () => void;
  onSuccess?: (profile: UserProfile) => void;
}

export interface FormData {
  full_name: string;
  github_username: string;
  university: string;
  nationality: string;
  state: string;
  district: string;
  description?: string;
}

export interface FormErrors {
  full_name?: string;
  github_username?: string;
  university?: string;
  nationality?: string;
  state?: string;
  district?: string;
}

const ProfileSetupModal: React.FC<ProfileSetupModalProps> = ({
  isOpen,
  onClose,
  onSuccess,
}) => {
  const [formData, setFormData] = useState<FormData>({
    full_name: "",
    github_username: "",
    university: "",
    nationality: "",
    state: "",
    district: "",
    description: "",
  });

  const [errors, setErrors] = useState<FormErrors>({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const [submitSuccess, setSubmitSuccess] = useState(false);

  // Dropdown data
  const [universities, setUniversities] = useState<string[]>([]);
  const [countries, setCountries] = useState<string[]>([]);
  const [states, setStates] = useState<string[]>([]);
  const [loadingUniversities, setLoadingUniversities] = useState(false);
  const [loadingCountries, setLoadingCountries] = useState(false);
  const [loadingStates, setLoadingStates] = useState(false);

  // Autocomplete state
  const [universitySearch, setUniversitySearch] = useState("");
  const [showUniversitySuggestions, setShowUniversitySuggestions] =
    useState(false);
  const [filteredUniversities, setFilteredUniversities] = useState<string[]>(
    []
  );

  // Load dropdown data when modal opens
  useEffect(() => {
    if (isOpen) {
      setFormData({
        full_name: "",
        github_username: "",
        university: "",
        nationality: "",
        state: "",
        district: "",
        description: "",
      });
      setErrors({});
      setSubmitError(null);
      setSubmitSuccess(false);
      setUniversitySearch("");
      setShowUniversitySuggestions(false);

      // Load universities and countries
      loadUniversities();
      loadCountries();
    }
  }, [isOpen]);

  // Load states when nationality changes
  useEffect(() => {
    if (formData.nationality) {
      loadStates(formData.nationality);
    } else {
      setStates([]);
    }
  }, [formData.nationality]);

  // Filter universities based on search
  useEffect(() => {
    if (universitySearch) {
      const filtered = universities.filter(
        (uni) =>
          typeof uni === "string" &&
          uni.toLowerCase().includes(universitySearch.toLowerCase())
      );
      setFilteredUniversities(filtered.slice(0, 10)); // Limit to 10 suggestions
    } else {
      setFilteredUniversities([]);
    }
  }, [universitySearch, universities]);

  const loadUniversities = async () => {
    try {
      setLoadingUniversities(true);
      const response = await profileAPI.getUniversities();
      setUniversities(response.universities || []);
    } catch (error) {
      console.error("Failed to load universities:", error);
    } finally {
      setLoadingUniversities(false);
    }
  };

  const loadCountries = async () => {
    try {
      setLoadingCountries(true);
      const response = await profileAPI.getCountries();
      setCountries(response.countries || []);
    } catch (error) {
      console.error("Failed to load countries:", error);
    } finally {
      setLoadingCountries(false);
    }
  };

  const loadStates = async (country: string) => {
    try {
      setLoadingStates(true);
      const response = await profileAPI.getStates(country);
      setStates(response.states || []);
    } catch (error) {
      console.error("Failed to load states:", error);
      setStates([]);
    } finally {
      setLoadingStates(false);
    }
  };

  const validateField = (
    name: keyof FormData,
    value: string
  ): string | undefined => {
    switch (name) {
      case "full_name":
        if (!value.trim()) return "Full name is required";
        if (value.trim().length < 2)
          return "Full name must be at least 2 characters";
        return undefined;

      case "github_username":
        if (!value.trim()) return "GitHub username is required";
        return undefined;

      case "university":
        if (!value.trim()) return "University is required";
        return undefined;

      case "nationality":
        if (!value.trim()) return "Nationality is required";
        return undefined;

      case "state":
        if (!value.trim()) return "State is required";
        return undefined;

      case "district":
        if (!value.trim()) return "District is required";
        return undefined;

      default:
        return undefined;
    }
  };

  const handleInputChange = (
    e: React.ChangeEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));

    // Clear error for this field when user starts typing
    if (errors[name as keyof FormErrors]) {
      setErrors((prev) => ({ ...prev, [name]: undefined }));
    }

    // Clear submit error when user makes changes
    if (submitError) {
      setSubmitError(null);
    }
  };

  const handleBlur = (
    e: React.FocusEvent<
      HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement
    >
  ) => {
    const { name, value } = e.target;
    const error = validateField(name as keyof FormData, value);
    if (error) {
      setErrors((prev) => ({ ...prev, [name]: error }));
    }
  };

  const validateForm = (): boolean => {
    const newErrors: FormErrors = {};

    Object.keys(formData).forEach((key) => {
      if (key !== "description") {
        const error = validateField(
          key as keyof FormData,
          formData[key as keyof FormData] || ""
        );
        if (error) {
          newErrors[key as keyof FormErrors] = error;
        }
      }
    });

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);
    setSubmitError(null);

    try {
      const profileData: ProfileSetupRequest = {
        full_name: formData.full_name.trim(),
        github_username: formData.github_username.trim(),
        university: formData.university.trim(),
        nationality: formData.nationality.trim(),
        state: formData.state.trim(),
        district: formData.district.trim(),
        description: formData.description?.trim(),
      };

      const response = await profileAPI.setupProfile(profileData);

      setSubmitSuccess(true);

      // Call success callback if provided
      if (onSuccess && response.profile) {
        onSuccess(response.profile);
      }

      // Trigger page refresh after profile setup to show rankings
      setTimeout(() => {
        onClose();
        // Refresh the page to reload all components with new profile data
        window.location.reload();
      }, 1500);
    } catch (error: any) {
      console.error("Profile setup error:", error);

      // Handle specific error cases
      if (error.status_code === 409) {
        setSubmitError(
          "Profile already exists. Please update your profile instead."
        );
      } else if (error.status_code === 400) {
        setSubmitError(
          error.message || "Invalid profile data. Please check your inputs."
        );
      } else if (error.status_code === 500) {
        setSubmitError("Server error. Please try again later.");
      } else {
        setSubmitError(
          error.message || "Failed to create profile. Please try again."
        );
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleClose = () => {
    if (!isSubmitting) {
      onClose();
    }
  };

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black bg-opacity-50">
        <motion.div
          initial={{ opacity: 0, scale: 0.95 }}
          animate={{ opacity: 1, scale: 1 }}
          exit={{ opacity: 0, scale: 0.95 }}
          transition={{ duration: 0.2 }}
          className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto"
          onClick={(e) => e.stopPropagation()}
        >
          {/* Header */}
          <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-bold text-gray-900">
                Complete Your Profile
              </h2>
              <p className="text-sm text-gray-600 mt-1">
                Set up your profile to see how you rank among peers
              </p>
            </div>
            <button
              onClick={handleClose}
              disabled={isSubmitting}
              className="p-2 rounded-lg hover:bg-gray-100 transition-colors disabled:opacity-50"
              aria-label="Close modal"
            >
              <X className="h-5 w-5 text-gray-500" />
            </button>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="p-6 space-y-6">
            {/* Full Name */}
            <div>
              <label
                htmlFor="full_name"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4" />
                  <span>Full Name *</span>
                </div>
              </label>
              <input
                type="text"
                id="full_name"
                name="full_name"
                value={formData.full_name}
                onChange={handleInputChange}
                onBlur={handleBlur}
                disabled={isSubmitting}
                className={`input-field ${
                  errors.full_name ? "input-error" : ""
                }`}
                placeholder="Enter your full name"
              />
              {errors.full_name && (
                <p className="mt-1 text-sm text-red-600">{errors.full_name}</p>
              )}
            </div>

            {/* GitHub Username */}
            <div>
              <label
                htmlFor="github_username"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                <div className="flex items-center space-x-2">
                  <Github className="h-4 w-4" />
                  <span>GitHub Username *</span>
                </div>
              </label>
              <input
                type="text"
                id="github_username"
                name="github_username"
                value={formData.github_username}
                onChange={handleInputChange}
                onBlur={handleBlur}
                disabled={isSubmitting}
                className={`input-field ${
                  errors.github_username ? "input-error" : ""
                }`}
                placeholder="Enter your GitHub username"
              />
              {errors.github_username && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.github_username}
                </p>
              )}
            </div>

            {/* University with Autocomplete */}
            <div className="relative">
              <label
                htmlFor="university"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                <div className="flex items-center space-x-2">
                  <Building2 className="h-4 w-4" />
                  <span>University *</span>
                </div>
              </label>
              <input
                type="text"
                id="university"
                name="university"
                value={universitySearch || formData.university}
                onChange={(e) => {
                  setUniversitySearch(e.target.value);
                  setFormData((prev) => ({
                    ...prev,
                    university: e.target.value,
                  }));
                  setShowUniversitySuggestions(true);
                  if (errors.university) {
                    setErrors((prev) => ({ ...prev, university: undefined }));
                  }
                }}
                onFocus={() => setShowUniversitySuggestions(true)}
                onBlur={(e) => {
                  // Delay to allow click on suggestion
                  setTimeout(() => {
                    setShowUniversitySuggestions(false);
                    handleBlur(e);
                  }, 200);
                }}
                disabled={isSubmitting || loadingUniversities}
                className={`input-field ${
                  errors.university ? "input-error" : ""
                }`}
                placeholder="Start typing your university name"
                autoComplete="off"
              />

              {/* Autocomplete Suggestions */}
              {showUniversitySuggestions && filteredUniversities.length > 0 && (
                <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                  {filteredUniversities.map((uni, index) => (
                    <button
                      key={index}
                      type="button"
                      onClick={() => {
                        setFormData((prev) => ({ ...prev, university: uni }));
                        setUniversitySearch(uni);
                        setShowUniversitySuggestions(false);
                      }}
                      className="w-full text-left px-4 py-2 hover:bg-primary-50 transition-colors text-sm"
                    >
                      {uni}
                    </button>
                  ))}
                </div>
              )}

              {loadingUniversities && (
                <p className="mt-1 text-sm text-gray-500">
                  Loading universities...
                </p>
              )}
              {errors.university && (
                <p className="mt-1 text-sm text-red-600">{errors.university}</p>
              )}
            </div>

            {/* Nationality Dropdown */}
            <div>
              <label
                htmlFor="nationality"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                <div className="flex items-center space-x-2">
                  <Globe className="h-4 w-4" />
                  <span>Nationality *</span>
                </div>
              </label>
              <select
                id="nationality"
                name="nationality"
                value={formData.nationality}
                onChange={(e) => {
                  handleInputChange(e);
                  // Reset state when country changes
                  setFormData((prev) => ({ ...prev, state: "", district: "" }));
                }}
                onBlur={handleBlur}
                disabled={isSubmitting || loadingCountries}
                className={`input-field ${
                  errors.nationality ? "input-error" : ""
                }`}
              >
                <option value="">Select your country</option>
                {countries.map((country, index) => (
                  <option key={index} value={country}>
                    {country}
                  </option>
                ))}
              </select>
              {loadingCountries && (
                <p className="mt-1 text-sm text-gray-500">
                  Loading countries...
                </p>
              )}
              {errors.nationality && (
                <p className="mt-1 text-sm text-red-600">
                  {errors.nationality}
                </p>
              )}
            </div>

            {/* State Cascading Dropdown */}
            <div>
              <label
                htmlFor="state"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                <div className="flex items-center space-x-2">
                  <MapPin className="h-4 w-4" />
                  <span>State *</span>
                </div>
              </label>
              {states.length > 0 ? (
                <select
                  id="state"
                  name="state"
                  value={formData.state}
                  onChange={handleInputChange}
                  onBlur={handleBlur}
                  disabled={isSubmitting || loadingStates}
                  className={`input-field ${errors.state ? "input-error" : ""}`}
                >
                  <option value="">Select your state</option>
                  {states.map((state, index) => (
                    <option key={index} value={state}>
                      {state}
                    </option>
                  ))}
                </select>
              ) : (
                <input
                  type="text"
                  id="state"
                  name="state"
                  value={formData.state}
                  onChange={handleInputChange}
                  onBlur={handleBlur}
                  disabled={isSubmitting || !formData.nationality}
                  className={`input-field ${errors.state ? "input-error" : ""}`}
                  placeholder={
                    formData.nationality
                      ? "Enter your state"
                      : "Select country first"
                  }
                />
              )}
              {loadingStates && (
                <p className="mt-1 text-sm text-gray-500">Loading states...</p>
              )}
              {errors.state && (
                <p className="mt-1 text-sm text-red-600">{errors.state}</p>
              )}
            </div>

            {/* District */}
            <div>
              <label
                htmlFor="district"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                <div className="flex items-center space-x-2">
                  <Map className="h-4 w-4" />
                  <span>District *</span>
                </div>
              </label>
              <input
                type="text"
                id="district"
                name="district"
                value={formData.district}
                onChange={handleInputChange}
                onBlur={handleBlur}
                disabled={isSubmitting}
                className={`input-field ${
                  errors.district ? "input-error" : ""
                }`}
                placeholder="Enter your district"
              />
              {errors.district && (
                <p className="mt-1 text-sm text-red-600">{errors.district}</p>
              )}
            </div>

            {/* Description (Optional) */}
            <div>
              <label
                htmlFor="description"
                className="block text-sm font-medium text-gray-700 mb-2"
              >
                Description (Optional)
              </label>
              <textarea
                id="description"
                name="description"
                value={formData.description}
                onChange={handleInputChange}
                disabled={isSubmitting}
                rows={3}
                className="input-field resize-none"
                placeholder="Tell us about yourself (optional)"
              />
            </div>

            {/* Error Message */}
            {submitError && (
              <div className="p-4 bg-red-50 border border-red-200 rounded-lg">
                <p className="text-sm text-red-600">{submitError}</p>
              </div>
            )}

            {/* Success Message */}
            {submitSuccess && (
              <div className="p-4 bg-green-50 border border-green-200 rounded-lg">
                <p className="text-sm text-green-600">
                  Profile created successfully!
                </p>
              </div>
            )}

            {/* Actions */}
            <div className="flex items-center justify-end space-x-3 pt-4 border-t border-gray-200">
              <button
                type="button"
                onClick={handleClose}
                disabled={isSubmitting}
                className="btn-ghost"
              >
                Cancel
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="btn-primary"
              >
                {isSubmitting ? "Creating Profile..." : "Create Profile"}
              </button>
            </div>
          </form>
        </motion.div>
      </div>
    </AnimatePresence>
  );
};

export default ProfileSetupModal;
