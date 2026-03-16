const jwt = require('jsonwebtoken');
const User = require('../models/User');
const StudentProfile = require('../models/StudentProfile');
const CompanyProfile = require('../models/CompanyProfile');
const AppError = require('../utils/appError');
const catchAsync = require('../utils/catchAsync');

const signToken = (id) => {
  return jwt.sign({ id }, process.env.JWT_SECRET, {
    expiresIn: process.env.JWT_EXPIRES_IN,
  });
};

const createSendToken = (user, statusCode, res) => {
  const token = signToken(user._id);

  // Remove password from output
  user.password = undefined;

  res.status(statusCode).json({
    status: 'success',
    token,
    data: {
      user,
    },
  });
};

exports.register = catchAsync(async (req, res, next) => {
  const { name, email, password, role, companyName } = req.body;

  // 1) Create the user
  const newUser = await User.create({
    name,
    email,
    password,
    role: role || 'student',
  });

  // 2) Create the corresponding profile
  if (newUser.role === 'student') {
    await StudentProfile.create({ user: newUser._id });
  } else if (newUser.role === 'company') {
    if (!companyName) {
      return next(new AppError('Please provide a company name for company registration', 400));
    }
    await CompanyProfile.create({ user: newUser._id, companyName });
  }

  createSendToken(newUser, 201, res);
});

exports.login = catchAsync(async (req, res, next) => {
  const { email, password } = req.body;

  // 1) Check if email and password exist
  if (!email || !password) {
    return next(new AppError('Please provide email and password!', 400));
  }

  // 2) Check if user exists & password is correct
  const user = await User.findOne({ email }).select('+password');

  if (!user || !(await user.correctPassword(password, user.password))) {
    return next(new AppError('Incorrect email or password', 401));
  }

  // 3) If everything ok, send token to client
  createSendToken(user, 200, res);
});

exports.getMe = catchAsync(async (req, res, next) => {
  let profile;
  if (req.user.role === 'student') {
    profile = await StudentProfile.findOne({ user: req.user._id });
  } else if (req.user.role === 'company') {
    profile = await CompanyProfile.findOne({ user: req.user._id });
  }

  res.status(200).json({
    status: 'success',
    data: {
      user: req.user,
      profile
    }
  });
});
