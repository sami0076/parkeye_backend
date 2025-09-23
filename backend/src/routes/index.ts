import { Router } from 'express';
import auth from './modules/auth.js';
import permits from './modules/permits.js';
import lots from './modules/lots.js';
import events from './modules/events.js';
import recommendations from './modules/recommendations.js';
import reservations from './modules/reservations.js';
import tickets from './modules/tickets.js';

export const router = Router();

router.use('/auth', auth);
router.use('/permits', permits);
router.use('/lots', lots);
router.use('/events', events);
router.use('/recommendations', recommendations);
router.use('/reservations', reservations);
router.use('/tickets', tickets);

